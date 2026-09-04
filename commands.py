import uuid
import html
import math
from aiogram import Router, types, F, Bot
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BotCommand

from config import ADMIN_ID
from database import (
    save_test_paper, 
    get_recent_tests, 
    get_total_tests_count, 
    get_user_tests_paginated, 
    get_all_tests_paginated, 
    delete_test_paper,
    get_test_paper
)
from pdf_generator import generate_and_send
from utils import parse_raw_text

router = Router()

class QuizForm(StatesGroup):
    waiting_for_topic = State()
    waiting_for_format = State()
    collecting_questions = State()

async def setup_bot_commands(bot_instance: Bot):
    commands = [
        BotCommand(command="start", description="🤖 बॉट शुरू करें"),
        BotCommand(command="create", description="📝 नया टेस्ट बनाएं"),
        BotCommand(command="prompt", description="✨ Gemini AI Prompt (फोटो/PDF से प्रश्न बनाएं)"),
        BotCommand(command="cancel", description="❌ चालू प्रक्रिया रद्द करें"),
        BotCommand(command="help", description="❓ सहायता एवं निर्देश"),
        BotCommand(command="mytests", description="📂 मेरे बनाए गए टेस्ट"),
        BotCommand(command="alltests", description="👑 सभी टेस्ट (केवल एडमिन)"),
        BotCommand(command="ppt", description="📊 PPT PDF बनाएं (/ppt ID)"),
        BotCommand(command="test", description="📄 Test PDF बनाएं (/test ID)"),
        BotCommand(command="answer", description="✅ Answer PDF बनाएं (/answer ID)"),
        BotCommand(command="stats", description="📈 कुल टेस्ट के आंकड़े"),
    ]
    await bot_instance.set_my_commands(commands)

def build_tests_markup(records, page, total_count, is_admin=False):
    """पेजिंग और डायरेक्ट एक्शन बटन्स (Test, Ans, PPT, Delete)"""
    keyboard = []
    page_size = 5
    total_pages = math.ceil(total_count / page_size) or 1

    for r in records:
        doc_id = r["_id"]
        topic = r.get("topic", "N/A")[:15]
        
        keyboard.append([
            InlineKeyboardButton(text=f"📌 {doc_id} | {topic}", callback_data=f"info_{doc_id}")
        ])
        keyboard.append([
            InlineKeyboardButton(text="📄 Test", callback_data=f"gen_test_{doc_id}"),
            InlineKeyboardButton(text="✅ Ans", callback_data=f"gen_answer_{doc_id}"),
            InlineKeyboardButton(text="📊 PPT", callback_data=f"gen_ppt_{doc_id}"),
            InlineKeyboardButton(text="🗑️ Delete", callback_data=f"del_{doc_id}_{page}_{'adm' if is_admin else 'usr'}")
        ])

    nav_buttons = []
    prefix = "adm_page" if is_admin else "usr_page"
    
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Prev", callback_data=f"{prefix}_{page - 1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"📑 {page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Next ▶️", callback_data=f"{prefix}_{page + 1}"))

    keyboard.append(nav_buttons)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.message(CommandStart(), StateFilter("*"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        "🤖 <b>Rajesh Competition Centre Bot में आपका स्वागत है!</b>\n\n"
        "यह बॉट प्रतियोगी परीक्षाओं के लिए क्विज, टेस्ट पेपर्स और PPT PDFs जनरेट करता है।\n\n"
        "📌 <b>उपलब्ध मुख्य कमांड्स:</b>\n"
        "• /create - नया टेस्ट बनाएं\n"
        "• /prompt - फोटो / PDF से AI प्रश्न बनाने का Prompt\n"
        "• /mytests - अपने बनाए टेस्ट देखें\n"
        "• /cancel - प्रक्रिया रद्द करें\n"
        "• /help - प्रयोग करने की गाइड\n"
        "• /stats - डेटाबेस के आंकड़े\n\n"
        "शुरू करने के लिए नीचे <b>'Create'</b> बटन दबाएं 👇"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Create (नया बनाएं)", callback_data="btn_create")],
        [InlineKeyboardButton(text="✨ AI Prompt (फोटो / PDF से प्रश्न)", callback_data="btn_prompt")],
        [InlineKeyboardButton(text="❓ सहायता (Help)", callback_data="btn_help")]
    ])
    await message.reply(welcome_text, reply_markup=keyboard)

@router.message(Command("cancel"), StateFilter("*"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.reply("ℹ️ कोई सक्रिय प्रक्रिया जारी नहीं है।")
        return
    
    await state.clear()
    await message.reply("❌ <b>चालू प्रक्रिया सफलतापूर्वक रद्द (Cancel) कर दी गई है!</b>\n\nनया टेस्ट बनाने के लिए /create टाइप करें।")

@router.message(Command("create"), StateFilter("*"))
async def cmd_create(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(QuizForm.waiting_for_topic)
    await message.reply("🎯 <b>कृपया अपने टेस्ट पेपर का नाम (Topic Name) दर्ज करें:</b>\n\n<i>(उदाहरण: हर्यक वंश एवं मगध साम्राज्य)</i>")

@router.message(Command("prompt"), StateFilter("*"))
@router.callback_query(F.data == "btn_prompt")
async def cmd_prompt(event: types.Message | CallbackQuery):
    prompt_text = (
        "✨ <b>Gemini AI क्विज़ मेकर प्रॉम्प्ट (Master Prompt)</b>\n\n"
        "अगर आपके पास किसी <b>किताब की फोटो, AI, PYQ, PDF या थ्योरी नोट्स</b> हैं, या फिर आप टॉपिक के नाम से प्रश्न बनवाना चाहते हैं, तो नीचे दिए गए बॉक्स पर क्लिक करके <b> Copy</b>  करें:\n\n"
        "<code>विषय/टॉपिक (Topic Name): [यहाँ अपना टॉपिक लिखें या खाली छोड़ें अगर PDF अटैच है]\n"
        "प्रश्नों की संख्या (Total Questions): [जितने प्रश्न चाहिए जैसे 30, 50 लिखें]\n\n"
        "कृपया दिए गए Photo / PDF / PYQ / थ्योरी नोट्स को ध्यान से पढ़ें और इनसे ऑब्जेक्टिव प्रश्न (MCQs) बनाकर मुझे बिल्कुल इसी फॉर्मेट में दें:\n\n"
        "1. भारत की राजधानी क्या है?\n"
        "a) मुंबई\n"
        "b) नई दिल्ली ✅\n"
        "c) कोलकाता\n"
        "d) चेन्नई\n\n"
        "नियम (Strict Rules):\n"
        "1. जो उत्तर सही (Correct Answer) हो, उसके विकल्प के अंत में अनिवार्य रूप से '✅' ग्रीन टिक लगाएं।\n"
        "2. अगर यह थ्योरी नोट्स हैं, तो उससे सबसे महत्वपूर्ण प्रश्न खुद बनाएं।\n"
        "3. अगर यह फोटो या PDF है, तो उसमें मौजूद सभी प्रश्नों को ऊपर दिए गए फॉर्मेट में डिजिटल टेक्स्ट में बदलें।\n"
        "4. उत्तर देने में कोई भी फालतू बात या परिचय न लिखें। सिर्फ और सिर्फ प्रश्नों की लिस्ट दें।\n"
        "5. आपके द्वारा दिए जाने वाले सारे के सारे प्रश्न एक ही सिंगल कोडिंग बॉक्स (Code Block) के अंदर होने चाहिए, ताकि एक क्लिक में पूरा टेक्स्ट कॉपी किया जा सके।</code>\n\n"
        "📌 <b>उपयोग करने की विधि:</b>\n"
        "1. ऊपर दिए गए कोड पर टैप करके <b> Copy</b>  करें।\n"
        "2. <b> Google Gemini App</b>  (या चैट) में जाएं।\n"
        "3. अपनी फोटो / PDF अटैच करें (या बिना अटैच किए टॉपिक और प्रश्नों की संख्या भरें) और यह Prompt पेस्ट करके भेजें।\n"
        "4. Gemini से मिले उत्तर को सीधे कॉपी करके यहाँ बॉट में <b>/create</b> दबाकर पेस्ट कर दें!"
    )
    if isinstance(event, CallbackQuery):
        await event.message.reply(prompt_text)
        await event.answer()
    else:
        await event.reply(prompt_text)

@router.message(Command("help"), StateFilter("*"))
@router.callback_query(F.data == "btn_help")
async def cmd_help(event: types.Message | CallbackQuery):
    help_text = (
        "📖 <b>RCC Quiz Bot - गाइड एवं सहायता</b>\n\n"
        "<b>1. प्रश्न कैसे भेजें?</b>\n"
        "प्रश्न निम्न फॉर्मेट में भेजें:\n"
        "<code>1. भारत की राजधानी क्या है?\n"
        "a) मुंबई\n"
        "b) नई दिल्ली ✅\n"
        "c) कोलकाता\n"
        "d) चेन्नई</code>\n\n"
        "<b>2. फोटो / PDF से प्रश्न कैसे बनाएं?</b>\n"
        "• /prompt कमांड टाइप करें और दिए गए प्रॉम्प्ट को Gemini AI में उपयोग करें।\n\n"
        "<b>3. ID से पुनः PDF डाउनलोड करना:</b>\n"
        "• PPT के लिए: <code>/ppt &lt;ID&gt;</code>\n"
        "• केवल प्रश्नों के लिए: <code>/test &lt;ID&gt;</code>\n"
        "• उत्तर कुंजी सहित: <code>/answer &lt;ID&gt;</code>\n\n"
        "<b>4. प्रक्रिया रद्द करना:</b>\n"
        "किसी भी समय /cancel भेजकर प्रक्रिया रोक सकते हैं।"
    )
    if isinstance(event, CallbackQuery):
        await event.message.reply(help_text)
        await event.answer()
    else:
        await event.reply(help_text)

# 📂 /mytests - अपने बनाए गए सभी टेस्ट पेज बाय पेज देखें
@router.message(Command("mytests"), StateFilter("*"))
async def cmd_mytests(message: types.Message):
    page = 1
    user_id = message.from_user.id
    records, total = get_user_tests_paginated(user_id, page=page)
    
    if not records:
        await message.reply("📂 आपने अभी तक कोई टेस्ट पेपर नहीं बनाया है।")
        return

    text = f"📂 <b>आपके बनाए गए टेस्ट पेपर्स (कुल: {total}):</b>"
    markup = build_tests_markup(records, page, total, is_admin=False)
    await message.reply(text, reply_markup=markup)

@router.callback_query(F.data.startswith("usr_page_"))
async def nav_user_tests(callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    records, total = get_user_tests_paginated(user_id, page=page)
    
    text = f"📂 <b>आपके बनाए गए टेस्ट पेपर्स (कुल: {total}):</b>"
    markup = build_tests_markup(records, page, total, is_admin=False)
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()

# 👑 /alltests - एडमिन के लिए बॉट के सभी क्विज़ का एक्सेस
@router.message(Command("alltests"), StateFilter("*"))
async def cmd_alltests(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("⚠️ यह कमांड केवल एडमिन के लिए है!")
        return

    page = 1
    records, total = get_all_tests_paginated(page=page)
    if not records:
        await message.reply("📂 डेटाबेस में कोई भी टेस्ट मौजूद नहीं है।")
        return

    text = f"👑 <b>सभी यूज़र्स के टेस्ट पेपर्स (ADMIN VIEW - कुल: {total}):</b>"
    markup = build_tests_markup(records, page, total, is_admin=True)
    await message.reply(text, reply_markup=markup)

@router.callback_query(F.data.startswith("adm_page_"))
async def nav_admin_tests(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⚠️ अनुमति नहीं है!", show_alert=True)
        return

    page = int(callback.data.split("_")[2])
    records, total = get_all_tests_paginated(page=page)
    
    text = f"👑 <b>सभी यूज़र्स के टेस्ट पेपर्स (ADMIN VIEW - कुल: {total}):</b>"
    markup = build_tests_markup(records, page, total, is_admin=True)
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()

# direct PDF button trigger
@router.callback_query(F.data.startswith("gen_"))
async def handle_direct_gen(callback: CallbackQuery, bot: Bot):
    _, gen_type_key, doc_id = callback.data.split("_")
    type_map = {"test": "Test PDF", "answer": "Answer Test PDF", "ppt": "PPT"}
    gen_type = type_map.get(gen_type_key, "Test PDF")
    
    row = get_test_paper(doc_id)
    if not row:
        await callback.answer("❌ ID नहीं मिला!", show_alert=True)
        return
        
    if row.get("user_id") and row.get("user_id") != callback.from_user.id and callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ यह आपके द्वारा नहीं बनाया गया है!", show_alert=True)
        return

    await callback.answer(f"⏳ {gen_type} बनाया जा रहा है...")
    try:
        await generate_and_send(bot, callback.message.chat.id, doc_id, gen_type)
    except Exception as e:
        await callback.message.reply(f"❌ Error: {html.escape(str(e))}")

# Delete Button Handler
@router.callback_query(F.data.startswith("del_"))
async def handle_delete_test(callback: CallbackQuery):
    _, doc_id, page_str, mode = callback.data.split("_")
    page = int(page_str)
    is_admin = (mode == "adm")

    row = get_test_paper(doc_id)
    if not row:
        await callback.answer("❌ ID नहीं मिला!", show_alert=True)
        return

    if row.get("user_id") and row.get("user_id") != callback.from_user.id and callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ आप इसे डिलीट नहीं कर सकते!", show_alert=True)
        return

    if delete_test_paper(doc_id):
        await callback.answer("✅ टेस्ट डिलीट हो गया!", show_alert=True)
        if is_admin:
            records, total = get_all_tests_paginated(page=page)
        else:
            records, total = get_user_tests_paginated(callback.from_user.id, page=page)

        if not records and page > 1:
            page -= 1
            records, total = get_all_tests_paginated(page) if is_admin else get_user_tests_paginated(callback.from_user.id, page)

        if not records:
            await callback.message.edit_text("📂 अब कोई टेस्ट मौजूद नहीं है।")
        else:
            text = f"{'👑 <b>सभी यूज़र्स के टेस्ट' if is_admin else '📂 <b>आपके बनाए गए टेस्ट'} पेपर्स (कुल: {total}):</b>"
            markup = build_tests_markup(records, page, total, is_admin=is_admin)
            await callback.message.edit_text(text, reply_markup=markup)

@router.message(Command("stats"), StateFilter("*"))
async def cmd_stats(message: types.Message):
    try:
        count = get_total_tests_count()
        await message.reply(f"📊 <b>डेटाबेस आंकड़े:</b>\n\nकुल सेव किए गए टेस्ट पेपर्स: <b>{count}</b>")
    except Exception as e:
        await message.reply(f"❌ <b>Error:</b> {html.escape(str(e))}")

@router.callback_query(F.data == "btn_create")
async def ask_topic(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(QuizForm.waiting_for_topic)
    await callback.message.edit_text("🎯 <b>कृपया अपने टेस्ट पेपर का नाम (Topic Name) दर्ज करें:</b>")

@router.message(QuizForm.waiting_for_topic)
async def process_topic(message: types.Message, state: FSMContext):
    await state.update_data(topic=message.text.strip())
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 PPT (पीपीटी)", callback_data="fmt_PPT")],
        [InlineKeyboardButton(text="📄 Test PDF (टेस्ट पीडीएफ)", callback_data="fmt_Test PDF")],
        [InlineKeyboardButton(text="✅ Answer Test PDF (आंसर सहित)", callback_data="fmt_Answer Test PDF")]
    ])
    await message.reply("📝 <b>टॉपिक सेव हो गया!</b>\n\nअब चुनें कि किस फॉर्मेट में जनरेट करना चाहते हैं:", reply_markup=keyboard)
    await state.set_state(QuizForm.waiting_for_format)

@router.callback_query(QuizForm.waiting_for_format)
async def ask_questions(callback: CallbackQuery, state: FSMContext):
    fmt = callback.data.replace("fmt_", "")
    await state.update_data(selected_format=fmt, raw_questions="")
    
    sample = (
        "1. भारत की राजधानी क्या है?\n"
        "a) मुंबई\n"
        "b) नई दिल्ली ✅\n"
        "c) कोलकाता\n"
        "d) चेन्नई"
    )
    
    msg = (
        f"✅ आपने <b>{fmt}</b> चुना है।\n\n"
        "👇 <b>कृपया अपने प्रश्न इस फॉर्मेट में भेजें:</b>\n"
        f"<code>{sample}</code>\n\n"
        "📌 <i>नोट: प्रश्न भेजने के बाद <b>/done</b> टाइप करें।\n"
        "रद्द करने के लिए <b>/cancel</b> दबाएं।</i>"
    )
    await callback.message.edit_text(msg)
    await state.set_state(QuizForm.collecting_questions)

@router.message(QuizForm.collecting_questions)
async def collect_questions(message: types.Message, state: FSMContext, bot: Bot):
    text = message.text.strip()
    
    if text.startswith('/') and text.lower() != '/done':
        return

    if text.lower() == '/done':
        user_data = await state.get_data()
        raw_text = user_data.get('raw_questions', '')
        topic = user_data.get('topic', 'Test')
        selected_format = user_data.get('selected_format', 'Test PDF')
        
        if not raw_text.strip():
            await message.reply("❌ कोई प्रश्न नहीं मिला! कृपया पहले प्रश्न भेजें।")
            return

        doc_id = uuid.uuid4().hex[:6].upper()
        
        try:
            save_test_paper(doc_id, topic, raw_text, message.from_user.id)
        except Exception as e:
            await message.reply(f"❌ <b>Database Insert Failed:</b> {html.escape(str(e))}")
            return

        success_msg = (
            f"✅ <b>डेटा सेव हो गया!</b>\n\n"
            f"🔑 <b>आपकी Test ID:</b> <code>{doc_id}</code>\n\n"
            f"💡 <b>भविष्य में इस ID से डाउनलोड करें:</b>\n"
            f"• PPT: <code>/ppt {doc_id}</code>\n"
            f"• Test PDF: <code>/test {doc_id}</code>\n"
            f"• Answer PDF: <code>/answer {doc_id}</code>\n\n"
            f"<i>अभी आपका ({selected_format}) जनरेट किया जा रहा है...</i>"
        )
        await message.reply(success_msg)
        await state.clear()
        
        try:
            await generate_and_send(bot, message.chat.id, doc_id, selected_format)
        except Exception as e:
            await message.reply(f"❌ <b>Error:</b> {html.escape(str(e))}")
        return

    user_data = await state.get_data()
    current_raw = user_data.get('raw_questions', '')
    new_raw = current_raw + "\n\n" + text if current_raw else text
    await state.update_data(raw_questions=new_raw)
    
    parsed = parse_raw_text(new_raw)
    await message.reply(f"📥 <b>प्रश्न जोड़ दिए गए! (कुल: {len(parsed)})</b>\nऔर प्रश्न भेजें या <b>/done</b> टाइप करें।")

# 🔗 पुराने वाले ID कमांड्स (Exact same behaviour kept)
@router.message(Command("ppt"), StateFilter("*"))
async def cmd_ppt(message: types.Message, bot: Bot):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("⚠️ कृपया ID दर्ज करें। उदाहरण: <code>/ppt A1B2C3</code>")
        return
    try:
        await generate_and_send(bot, message.chat.id, args[1].strip().upper(), "PPT")
    except Exception as e:
        await message.reply(f"❌ <b>Error:</b> {html.escape(str(e))}")

@router.message(Command("test"), StateFilter("*"))
async def cmd_test(message: types.Message, bot: Bot):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("⚠️ कृपया ID दर्ज करें। उदाहरण: <code>/test A1B2C3</code>")
        return
    try:
        await generate_and_send(bot, message.chat.id, args[1].strip().upper(), "Test PDF")
    except Exception as e:
        await message.reply(f"❌ <b>Error:</b> {html.escape(str(e))}")

@router.message(Command("answer"), StateFilter("*"))
async def cmd_answer(message: types.Message, bot: Bot):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("⚠️ कृपया ID दर्ज करें। उदाहरण: <code>/answer A1B2C3</code>")
        return
    try:
        await generate_and_send(bot, message.chat.id, args[1].strip().upper(), "Answer Test PDF")
    except Exception as e:
        await message.reply(f"❌ <b>Error:</b> {html.escape(str(e))}")
