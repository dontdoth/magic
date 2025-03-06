import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import psutil
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from info import Config, Txt

config_path = Path("config.json")

def format_size(size):
    """تبدیل سایز به فرمت خوانا"""
    if not size:
        return ""
    power = 2**10
    n = 0
    units = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{round(size, 2)} {units[n]}B"

@Client.on_callback_query()
async def handle_query(bot: Client, query: CallbackQuery):
    """مدیریت دکمه‌های شیشه‌ای"""
    data = query.data

    try:
        if data == "help":
            help_buttons = [
                [
                    InlineKeyboardButton(text='📌 کانال هدف', callback_data='targetchnl'),
                    InlineKeyboardButton(text='🗑 حذف پیکربندی', callback_data='delete_conf')
                ],
                [
                    InlineKeyboardButton(text='👥 اکانت‌های تلگرام', callback_data='account_config'),
                    InlineKeyboardButton(text='🔙 بازگشت', callback_data='home')
                ]
            ]
            await query.message.edit(
                text=Txt.HELP_MSG,
                reply_markup=InlineKeyboardMarkup(help_buttons)
            )

        elif data == "server":
            msg = await query.message.edit(text="در حال پردازش...")
            
            uptime = time.strftime(
                "%H ساعت %M دقیقه %S ثانیه",
                time.gmtime(time.time() - Config.BOT_START_TIME)
            )
            
            total, used, free = shutil.disk_usage(".")
            system_info = f"""<b>💻 وضعیت سرور</b>

⏱ زمان آنلاین: <code>{uptime}</code>
🔄 مصرف CPU: <code>{psutil.cpu_percent()}%</code>
💾 مصرف RAM: <code>{psutil.virtual_memory().percent}%</code>
💽 فضای کل: <code>{format_size(total)}</code>
📊 فضای مصرفی: <code>{format_size(used)} ({psutil.disk_usage('/').percent}%)</code>
✨ فضای آزاد: <code>{format_size(free)}</code>"""

            await msg.edit_text(
                text=system_info,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(text='🔙 بازگشت', callback_data='home')
                ]])
            )

        elif data == "about":
            bot_info = await bot.get_me()
            await query.message.edit(
                text=Txt.ABOUT_MSG.format(bot_info.username, bot_info.username),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(text='🔙 بازگشت', callback_data='home')
                ]])
            )

        elif data == "home":
            main_buttons = [
                [
                    InlineKeyboardButton(text='💡 راهنما', callback_data='help'),
                    InlineKeyboardButton(text='📊 وضعیت سرور', callback_data='server')
                ],
                [
                    InlineKeyboardButton(text='📢 کانال آپدیت‌ها', url='https://t.me/EAGLE_UPDTAES'),
                    InlineKeyboardButton(text='ℹ️ درباره ما', callback_data='about')
                ],
                [
                    InlineKeyboardButton(text='👨‍💻 توسعه‌دهنده', url='https://t.me/its_deva_heree')
                ]
            ]
            
            await query.message.edit(
                text=Txt.START_MSG.format(query.from_user.mention),
                reply_markup=InlineKeyboardMarkup(main_buttons)
            )

        elif data == "delete_conf":
            if query.from_user.id != Config.OWNER:
                return await query.message.edit(
                    "⛔️ شما دسترسی لازم برای این عملیات را ندارید",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(text='🔙 بازگشت', callback_data='help')
                    ]])
                )
                
            confirm_buttons = [
                [InlineKeyboardButton(text='✅ بله', callback_data='delconfig-yes')],
                [InlineKeyboardButton(text='❌ خیر', callback_data='delconfig-no')]
            ]

            await query.message.edit(
                text="⚠️ آیا مطمئن هستید؟\n\nآیا می‌خواهید پیکربندی را حذف کنید؟",
                reply_markup=InlineKeyboardMarkup(confirm_buttons)
            )

        elif data == "targetchnl":
            if not config_path.exists():
                return await query.message.edit(
                    text="شما هنوز پیکربندی نساخته‌اید!\n\nابتدا با دستور /make_config پیکربندی بسازید",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(text='🔙 بازگشت', callback_data='help')
                    ]])
                )

            with open(config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)

            channel_info = await bot.get_chat(config['Target'])
            
            target_buttons = [
                [InlineKeyboardButton(text='🔄 تغییر کانال هدف', callback_data='chgtarget')],
                [InlineKeyboardButton(text='🔙 بازگشت', callback_data='help')]
            ]

            info_text = f"""📑 اطلاعات کانال:
            
📌 نام: <code>{channel_info.title}</code>
🔗 نام کاربری: <code>@{channel_info.username}</code>
🆔 شناسه: <code>{channel_info.id}</code>"""

            await query.message.edit(
                text=info_text,
                reply_markup=InlineKeyboardMarkup(target_buttons)
            )

        elif data == "chgtarget":
            try:
                with open(config_path, 'r', encoding='utf-8') as file:
                    config = json.load(file)

                try:
                    target = await bot.ask(
                        text=Txt.SEND_TARGET_CHANNEL,
                        chat_id=query.message.chat.id,
                        filters=filters.text,
                        timeout=60
                    )
                except:
                    await bot.send_message(
                        query.from_user.id,
                        "❌ خطا! درخواست منقضی شد\nلطفا با دستور /target دوباره تلاش کنید",
                        reply_to_message_id=target.id
                    )
                    return

                msg = await query.message.reply_text(
                    "⏳ لطفاً صبر کنید...",
                    reply_to_message_id=query.message.id
                )

                channel_id = target.text
                clean_id = re.sub("(@)|(https://)|(http://)|(t.me/)", "", channel_id)

                for account in config['accounts']:
                    try:
                        process = subprocess.Popen(
                            ["python", "login.py", clean_id, account['Session_String']],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                        )
                        
                        stdout, stderr = process.communicate()
                        
                        if process.wait() != 0:
                            print("خطا در اجرای دستور:", stderr)
                            return await query.message.edit(
                                '❌ خطایی رخ داد! لطفاً ورودی‌های خود را بررسی کنید'
                            )
                            
                        print("خروجی دستور:", stdout.decode('utf-8'))

                    except Exception as err:
                        await bot.send_message(
                            msg.chat.id,
                            f"<b>خطا:</b>\n<pre>{err}</pre>"
                        )

                new_config = {
                    "Target": clean_id,
                    "accounts": config['accounts']
                }

                with open(config_path, 'w', encoding='utf-8') as file:
                    json.dump(new_config, file, indent=4)

                await msg.edit("✅ کانال هدف با موفقیت بروزرسانی شد\n\nبرای مشاهده از دستور /target استفاده کنید")
                
            except Exception as e:
                print(f'خطا در خط {sys.exc_info()[-1].tb_lineno}: {type(e).__name__} - {str(e)}')

        elif data.startswith('delconfig'):
            condition = data.split('-')[1]
            try:
                if condition == 'yes':
                    os.remove('config.json')
                    await query.message.edit("✅ پیکربندی با موفقیت حذف شد")
                else:
                    await query.message.edit("❌ عملیات حذف لغو شد")
            except Exception as e:
                await query.message.edit(f"خطا: {e}")

        elif data == "account_config":
            if not config_path.exists():
                return await query.message.edit(
                    text="شما هنوز پیکربندی نساخته‌اید!\n\nابتدا با دستور /make_config پیکربندی بسازید",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(text='🔙 بازگشت', callback_data='help')
                    ]])
                )

            with open(config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)

            account_buttons = []
            for account in config["accounts"]:
                account_buttons.append([
                    InlineKeyboardButton(
                        text=f"👤 {account['OwnerName']}",
                        callback_data=str(account["OwnerUid"])
                    )
                ])

            account_buttons.append([
                InlineKeyboardButton(text='🔙 بازگشت', callback_data='help')
            ])

            await query.message.edit(
                text="📱 اکانت‌های تلگرام اضافه شده:",
                reply_markup=InlineKeyboardMarkup(account_buttons)
            )

        elif int(data) in [acc['OwnerUid'] for acc in json.load(open("config.json"))['accounts']]:
            account_data = {}
            for account in json.load(open("config.json"))['accounts']:
                if int(data) == account["OwnerUid"]:
                    account_data.update({
                        'Name': account['OwnerName'],
                        'UserId': account['OwnerUid']
                    })

            await query.message.edit(
                text=Txt.ACCOUNT_INFO.format(
                    account_data.get('Name'),
                    account_data.get('UserId')
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(text='🔙 بازگشت', callback_data='help')
                ]])
            )
            account_data = {}

    except Exception as e:
        print(f'خطا در خط {sys.exc_info()[-1].tb_lineno}: {type(e).__name__} - {str(e)}')
        await query.answer("❌ خطایی رخ داد! لطفاً دوباره تلاش کنید.")
