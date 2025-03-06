import os
import sys
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from info import Config, Txt

@Client.on_message(filters.private & filters.command('start'))
async def handle_start(bot: Client, message: Message):
    """مدیریت دستور استارت"""
    
    buttons = [
        [
            InlineKeyboardButton(text='💡 راهنما', callback_data='help'),
            InlineKeyboardButton(text='📊 وضعیت سرور', callback_data='server')
        ],
        [
            InlineKeyboardButton(text='📢 کانال آپدیت‌ها', url='https://t.me/lS_DEMIR'),
            InlineKeyboardButton(text='ℹ️ درباره ما', callback_data='about')
        ],
        [
            InlineKeyboardButton(text='👨‍💻 توسعه‌دهنده', url='https://t.me/lS_DEMIR')
        ]
    ]

    await message.reply_text(
        text=Txt.START_MSG.format(message.from_user.mention),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_message(filters.private & filters.command("restart") & filters.user(Config.SUDO))
async def restart_bot(bot: Client, message: Message):
    """راه‌اندازی مجدد ربات - فقط برای ادمین‌ها"""
    
    await message.reply_text("🔄 در حال راه‌اندازی مجدد...")
    
    # راه‌اندازی مجدد برنامه
    os.execl(sys.executable, sys.executable, *sys.argv)
