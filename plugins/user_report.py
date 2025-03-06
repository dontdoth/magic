import json
import os
import subprocess
from pathlib import Path
import sys
from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from pyrogram.errors import MessageIdInvalid
from info import Config, Txt

config_path = Path("config.json")

# دلایل گزارش
REPORT_REASONS = {
    '1': 'گزارش سوء استفاده از کودکان',
    '2': 'گزارش محتوای دارای کپی‌رایت',
    '3': 'گزارش جعل هویت',
    '4': 'گزارش گروه نامرتبط',
    '5': 'گزارش مواد مخدر غیرقانونی',
    '6': 'گزارش خشونت',
    '7': 'گزارش اطلاعات شخصی توهین‌آمیز',
    '8': 'گزارش محتوای پورنوگرافی',
    '9': 'گزارش اسپم'
}

async def send_report(reason_number: str):
    """ارسال گزارش با دلیل مشخص شده"""
    try:
        reason = REPORT_REASONS[reason_number]
        
        process = subprocess.Popen(
            ["python", "report.py", reason],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = process.communicate()
        
        if process.wait() == 0:
            print("خروجی دستور:", stdout)
            return [stdout, True]
        else:
            print("خطا در اجرای دستور:", stderr)
            return f"❌ خطا در ارسال گزارش:\n<code>{stderr}</code>"
            
    except Exception as e:
        print(f"خطا: {e}")
        return f"❌ خطای سیستمی: {e}"

async def handle_report_choice(bot: Client, msg: Message, reason_number: str):
    """مدیریت انتخاب دلیل گزارش"""
    
    if not config_path.exists():
        return await msg.reply_text(
            "⚠️ ابتدا باید پیکربندی را ایجاد کنید\n\nاز دستور /make_config استفاده کنید",
            reply_markup=ReplyKeyboardRemove()
        )

    with open(config_path, 'r', encoding='utf-8') as file:
        config = json.load(file)

    # بررسی وجود گزارش در حال انجام
    if Path('report.txt').exists():
        return await msg.reply_text(
            "⏳ یک گزارش در حال انجام است. لطفاً صبر کنید",
            reply_to_message_id=msg.id
        )

    try:
        # دریافت تعداد گزارش
        report_count = await bot.ask(
            text=Txt.SEND_NO_OF_REPORT_MSG.format(config['Target']),
            chat_id=msg.chat.id,
            filters=filters.text,
            timeout=30,
            reply_markup=ReplyKeyboardRemove()
        )
    except:
        await bot.send_message(
            msg.from_user.id,
            "❌ درخواست منقضی شد\nلطفاً با /report دوباره تلاش کنید"
        )
        return

    status_msg = await bot.send_message(
        chat_id=msg.chat.id,
        text="⏳ لطفاً صبر کنید...",
        reply_to_message_id=msg.id,
        reply_markup=ReplyKeyboardRemove()
    )

    if not report_count.text.isnumeric():
        await msg.reply_text(
            "❌ لطفاً یک عدد معتبر وارد کنید\n\nدوباره تلاش کنید: /report"
        )
        return

    try:
        count = int(report_count.text)
        for i in range(count):
            result = await send_report(reason_number)
            
            if result[1]:
                output = result[0].decode('utf-8').replace('\r\n', '\n')
                with open('report.txt', 'a+') as file:
                    file.write(output)
            else:
                await bot.send_message(
                    chat_id=msg.chat.id,
                    text=result,
                    reply_to_message_id=msg.id
                )
                return

    except Exception as e:
        print(f'خطا در خط {sys.exc_info()[-1].tb_lineno}: {type(e).__name__} - {e}')
        return await msg.reply_text(f"❌ خطا: {e}")

    await status_msg.delete()
    
    # ارسال نتیجه
    success_text = f"✅ گزارش با موفقیت به @{config['Target']} ارسال شد\n\n🔢 تعداد: {count} بار"
    await msg.reply_text(success_text)
    
    # ذخیره لاگ
    with open('report.txt', 'a') as file:
        file.write(f"\n\n{success_text}")
    
    # ارسال فایل لاگ
    await bot.send_document(
        chat_id=msg.chat.id,
        document='report.txt',
        reply_to_message_id=msg.id
    )
    
    os.remove('report.txt')

@Client.on_message(filters.private & filters.user(Config.OWNER) & filters.command('report'))
async def start_report(bot: Client, msg: Message):
    """شروع فرآیند گزارش"""
    
    keyboard = [
        [("۱"), ("۲")], [("۳"), ("۴")], 
        [("۵"), ("۶")], [("۷"), ("۸")],
        [("۹")]
    ]

    await bot.send_message(
        chat_id=msg.from_user.id,
        text=Txt.REPORT_CHOICE,
        reply_to_message_id=msg.id,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# مدیریت انتخاب‌های کاربر
for number in range(1, 10):
    @Client.on_message(filters.regex(str(number)))
    async def handle_choice(bot: Client, msg: Message):
        await handle_report_choice(bot, msg, msg.text)
