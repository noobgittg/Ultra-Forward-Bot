import os
import sys
import asyncio
import logging
import logging.config
import aiohttp
from database import db
from config import Config
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait
from aiohttp import web
from plugins.silicon import web_server

logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

RESTART_INTERVAL = 7 * 24 * 60 * 60
KEEP_ALIVE_URL = "https://severe-stace-compressor-7859af9e.koyeb.app/"
KEEP_ALIVE_INTERVAL = 45


async def keep_service_alive():
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        while True:
            try:
                await session.get(KEEP_ALIVE_URL)
                logging.info("💓 Keep-alive ping sent.")
            except Exception as e:
                logging.warning(f"⚠️ Keep-alive failed: {e}")
            await asyncio.sleep(KEEP_ALIVE_INTERVAL)


class Bot(Client):
    def __init__(self):
        super().__init__(
            Config.BOT_SESSION,
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            sleep_threshold=2000,
            workers=200,
            plugins={"root": "plugins"}
        )

    async def start(self):
        await super().start()
        me = await self.get_me()

        self.id = me.id
        self.username = me.username
        self.first_name = me.first_name
        self.set_parse_mode(ParseMode.HTML)

        logging.info(
            f"✅ Bot Started: {me.first_name} (@{me.username}) | Pyrogram v{__version__} | Layer {layer}"
        )

        asyncio.create_task(self.restart_loop())
        asyncio.create_task(keep_service_alive())
        asyncio.create_task(self.start_web_server())

        
    async def start_web_server(self):
        app = await web_server()
        runner = web.AppRunner(app)
        await runner.setup()
        await web.TCPSite(runner, "0.0.0.0", 8080).start()
        logging.info("🌐 Web Server Running on port 8080")

    async def restart_loop(self):
        while True:
            await asyncio.sleep(RESTART_INTERVAL)
            try:
                await self.send_message(Config.LOG_CHANNEL, "♻️ Restarting bot automatically...")
                logging.info("♻️ Restart triggered.")
            except Exception as e:
                logging.warning(f"⚠️ Restart notify failed: {e}")
            os.execl(sys.executable, sys.executable, *sys.argv)

    async def stop(self, *args):
        await super().stop()
        logging.info(f"🛑 Bot Stopped: @{self.username}")


app = Bot()
app.run()
