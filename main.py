# ==================== RENDER WEB SERVER ====================

async def handle_ping(request):
    return web.Response(text="RCC Bot is Live!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render स्वचालित रूप से PORT पर्यावरण चर (Environment Variable) पास करता है
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    await start_web_server()  # Render के लिए पोर्ट चालू करेगा
    await setup_bot_commands(bot)
    print("\n🚀 RCC BOT IS LIVE AND RUNNING!\n")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
