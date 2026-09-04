import os
import copy
import asyncio
import tempfile
import html
from aiogram import Bot, types
from aiogram.enums import ChatAction
from pptx import Presentation
from docxtpl import DocxTemplate

from config import PPT_TEMPLATE, DOCX_TEMPLATE
from database import get_test_paper
from utils import parse_raw_text, convert_to_pdf, format_docx_option

async def generate_and_send(bot: Bot, chat_id: int, doc_id: str, gen_type: str):
    """MongoDB से डेटा निकालकर PDF फाइल जनरेट करके भेजता है"""
    msg = None
    try:
        row = get_test_paper(doc_id)
        if not row:
            await bot.send_message(chat_id, "❌ <b>ID नहीं मिला!</b> कृपया सही ID दर्ज करें।")
            return

        topic = row["topic"]
        raw_text = row["raw_text"]
        parsed_qs = parse_raw_text(raw_text)
        
        await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        msg = await bot.send_message(chat_id, f"⏳ <b>{gen_type}</b> जनरेट हो रहा है, कृपया प्रतीक्षा करें...")

        temp_dir = tempfile.gettempdir()
        safe_topic = "".join([c if c.isalnum() else "_" for c in topic])
        output_pdf = os.path.join(temp_dir, f"{safe_topic}_{gen_type}_{doc_id}.pdf")
        
        loop = asyncio.get_running_loop()

        if gen_type == "PPT":
            if not os.path.exists(PPT_TEMPLATE):
                await msg.edit_text("❌ <b>Template Missing:</b> `template.pptx` नहीं मिला!")
                return
                
            output_file = os.path.join(temp_dir, f"temp_{doc_id}.pptx")
            prs = Presentation(PPT_TEMPLATE)
            slide = prs.slides[0]
            
            for index, q in enumerate(parsed_qs, 1):
                cl_a = q['a'].replace("✅", "").replace("*", "").strip()
                cl_b = q['b'].replace("✅", "").replace("*", "").strip()
                cl_c = q['c'].replace("✅", "").replace("*", "").strip()
                cl_d = q['d'].replace("✅", "").replace("*", "").strip()
                
                replacements = {
                    '{{TOPIC}}': topic, 
                    '{{QUESTION}}': f"Q{index}. {q['text']}",
                    '{{OPTION_A}}': f"A) {cl_a}", 
                    '{{OPTION_B}}': f"B) {cl_b}",
                    '{{OPTION_C}}': f"C) {cl_c}", 
                    '{{OPTION_D}}': f"D) {cl_d}"
                }
                
                target_slide = slide if index == 1 else prs.slides.add_slide(prs.slide_layouts[6])
                if index != 1:
                    for shape in slide.shapes:
                        new_el = copy.deepcopy(shape.element)
                        target_slide.shapes._spTree.insert_element_before(new_el, 'p:extLst')
                
                for shape in target_slide.shapes:
                    if shape.has_text_frame:
                        for p in shape.text_frame.paragraphs:
                            full_p_text = "".join(r.text for r in p.runs)
                            for key, val in replacements.items():
                                if key in full_p_text or key in p.text:
                                    if len(p.runs) > 0:
                                        p.runs[0].text = p.text.replace(key, val)
                                        for r in p.runs[1:]: 
                                            r.text = ""
                                    else:
                                        p.text = p.text.replace(key, val)

            prs.save(output_file)
            await loop.run_in_executor(None, convert_to_pdf, output_file, temp_dir)

        else: # Word / DOCX Formats
            if not os.path.exists(DOCX_TEMPLATE):
                await msg.edit_text("❌ <b>Template Missing:</b> `template.docx` नहीं मिला!")
                return
                
            output_file = os.path.join(temp_dir, f"temp_{doc_id}.docx")
            doc = DocxTemplate(DOCX_TEMPLATE)
            show_answers = (gen_type == "Answer Test PDF")
            
            formatted_qs = []
            for i, q in enumerate(parsed_qs, 1):
                formatted_qs.append({
                    'id': i, 
                    'text': q['text'],
                    'a': format_docx_option("(a)", q['a'], show_answers),
                    'b': format_docx_option("(b)", q['b'], show_answers),
                    'c': format_docx_option("(c)", q['c'], show_answers),
                    'd': format_docx_option("(d)", q['d'], show_answers),
                })
            
            doc.render({'topic_name': topic, 'questions': formatted_qs})
            doc.save(output_file)
            await loop.run_in_executor(None, convert_to_pdf, output_file, temp_dir)

        generated_pdf_path = output_file.rsplit('.', 1)[0] + ".pdf"
        
        if os.path.exists(generated_pdf_path):
            if os.path.exists(output_pdf):
                os.remove(output_pdf)
            os.rename(generated_pdf_path, output_pdf)
            
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
            await bot.send_document(
                chat_id, 
                types.FSInputFile(output_pdf),
                caption=f"📄 आपका <b>{gen_type}</b> तैयार है!\n🆔 <b>ID:</b> <code>{doc_id}</code>"
            )
            if msg:
                await msg.delete()
        else:
            if msg:
                await msg.edit_text("❌ <b>PDF Generation Error:</b> PDF फाइल नहीं बन सकी।")

        # Cleanup Temp Files
        if os.path.exists(output_file): 
            os.remove(output_file)
        if os.path.exists(output_pdf): 
            os.remove(output_pdf)

    except Exception as e:
        error_msg = f"❌ <b>Error:</b> {html.escape(str(e))}"
        if msg:
            await msg.edit_text(error_msg)
        else:
            await bot.send_message(chat_id, error_msg)
