import asyncio
import logging
import logging.config
from database import db
from config import Config
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait
from aiohttp import web
from plugins import web_server

logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)


class Bot(Client):
    def __init__(self):
        super().__init__(
            Config.BOT_SESSION,
            api_hash=Config.API_HASH,
            api_id=Config.API_ID,
            bot_token=Config.BOT_TOKEN,
            sleep_threshold=200,
            workers=2000,
            plugins={"root": "plugins"}
        )
        self.log = logging

    async def start(self):
        await super().start()
        me = await self.get_me()

        logging.info(f"✅ Started: {me.first_name} | Pyrogram v{__version__} | Layer {layer} | Username @{me.username}")

        app = web.AppRunner(await web_server())
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", 8080).start()

        self.id = me.id
        self.username = me.username
        self.first_name = me.first_name
        self.set_parse_mode(ParseMode.DEFAULT)

        text = "<b>♻️ Bot Restarted Successfully!</b>"
        logging.info("🔄 Sending restart broadcast...")

        success = 0
        failed = 0

        users = await db.get_all_frwd()
        async for user in users:
            chat_id = user['user_id']
            try:
                await self.send_message(chat_id, text)
                success += 1
            except FloodWait as e:
                await asyncio.sleep(e.value + 1)
                await self.send_message(chat_id, text)
                success += 1
            except Exception:
                failed += 1

        if (success + failed) != 0:
            await db.rmve_frwd(all=True)
            logging.info(f"📨 Broadcast Summary | ✅ Success: {success} | ❌ Failed: {failed}")

    async def stop(self, *args):
        msg = f"🛑 @{self.username} Stopped."
        await super().stop()
        logging.info(msg)


app = Bot()
app.run()
