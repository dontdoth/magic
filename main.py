import logging
import logging.config
from datetime import datetime
from pytz import timezone
from aiohttp import web
import pyromod
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from info import Config
from plugins import web_server

# تنظیمات لاگ
logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

class ReportBot(Client):
    """کلاس اصلی ربات گزارش‌دهی"""
    
    def __init__(self):
        """مقداردهی اولیه"""
        super().__init__(
            name="ReportBot",
            in_memory=True,
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins={'root': 'plugins'}
        )
        self.mention = None
        self.username = None

    async def start(self):
        """راه‌اندازی ربات"""
        try:
            # شروع کلاینت
            await super().start()
            
            # دریافت اطلاعات ربات
            me = await self.get_me()
            self.mention = me.mention
            self.username = me.username

            # راه‌اندازی وب‌سرور
            app_runner = web.AppRunner(await web_server())
            await app_runner.setup()
            
            # تنظیم آدرس و پورت
            bind_address = "0.0.0.0"
            await web.TCPSite(
                app_runner,
                bind_address,
                Config.PORT
            ).start()

            # لاگ راه‌اندازی
            startup_msg = (
                f"✅ ربات {me.first_name} "
                f"با Pyrogram نسخه {__version__} "
                f"(لایه {layer}) "
                f"در @{me.username} "
                "راه‌اندازی شد"
            )
            logger.info(startup_msg)

            # ارسال پیام به مالک
            owner_msg = f"**🤖 ربات {me.first_name} با موفقیت راه‌اندازی شد**"
            await self.send_message(Config.OWNER, owner_msg)

        except Exception as e:
            logger.error(f"❌ خطا در راه‌اندازی ربات: {e}")
            raise

    async def stop(self, *args):
        """توقف ربات"""
        try:
            await super().stop()
            logger.info("⛔️ ربات متوقف شد")
        except Exception as e:
            logger.error(f"❌ خطا در توقف ربات: {e}")
            raise

def main():
    """تابع اصلی برنامه"""
    try:
        # ایجاد و اجرای ربات
        bot = ReportBot()
        bot.run()
    except Exception as e:
        logger.critical(f"❌ خطای بحرانی: {e}")
        raise

if __name__ == "__main__":
    main()
