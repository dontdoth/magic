import json
from pathlib import Path
import subprocess
import sys
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from info import Config, Txt

config_path = Path("config.json")

# دستور افزودن اکانت جدید
@Client.on_message(filters.private & filters.user(Config.SUDO) & filters.command('add_account'))
async def add_account(bot: Client, cmd: Message):
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
        else:
            return await cmd.reply_text(
                text="شما هنوز پیکربندی نساخته‌اید!\n\n ابتدا با دستور /make_config پیکربندی بسازید",
                reply_to_message_id=cmd.id
            )

        try:
            session = await bot.ask(
                text=Txt.SEND_SESSION_MSG,
                chat_id=cmd.chat.id,
                filters=filters.text,
                timeout=60
            )
        except:
            await bot.send_message(
                cmd.from_user.id,
                "خطا!\n\nزمان درخواست تمام شد.\nبا دستور /make_config دوباره شروع کنید",
                reply_to_message_id=session.id
            )
            return

        ms = await cmd.reply_text('**لطفاً صبر کنید...**', reply_to_message_id=cmd.id)

        # بررسی تکراری نبودن اکانت
        for account in config['accounts']:
            if account['Session_String'] == session.text:
                return await ms.edit(
                    text=f"**اکانت {account['OwnerName']} قبلاً در پیکربندی وجود دارد**\n\nخطا!"
                )

        # اجرای اسکریپت لاگین
        try:
            process = subprocess.Popen(
                ["python", f"login.py", f"{config['Target']}", f"{session.text}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as err:
            await bot.send_message(
                cmd.chat.id,
                text=f"<b>خطا:</b>\n<pre>{err}</pre>"
            )

        stdout, stderr = process.communicate()
        return_code = process.wait()

        if return_code == 0:
            output_string = stdout.decode('utf-8').replace('\r\n', '\n')
            AccountHolder = json.loads(output_string)
        else:
            print("خطا در اجرای دستور:")
            print(stderr)
            return await ms.edit('**خطایی رخ داد! لطفاً ورودی‌های خود را بررسی کنید**')

        # افزودن اکانت جدید به پیکربندی
        try:
            NewConfig = {
                "Target": config['Target'],
                "accounts": list(config['accounts'])
            }

            new_account = {
                "Session_String": session.text,
                "OwnerUid": AccountHolder['id'],
                "OwnerName": AccountHolder['first_name']
            }
            NewConfig["accounts"].append(new_account)

            with open(config_path, 'w', encoding='utf-8') as file:
                json.dump(NewConfig, file, indent=4)

        except Exception as e:
            print(e)

        await ms.edit(
            text="**اکانت با موفقیت اضافه شد**\n\nبرای مشاهده همه اکانت‌های اضافه شده روی دکمه زیر کلیک کنید 👇",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    text='اکانت‌های اضافه شده',
                    callback_data='account_config'
                )
            ]])
        )

    except Exception as e:
        print('خطا در خط {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)

# دستور مشاهده کانال هدف
@Client.on_message(filters.private & filters.user(Config.SUDO) & filters.command('target'))
async def target(bot: Client, cmd: Message):
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
        else:
            return await cmd.reply_text(
                text="شما هنوز پیکربندی نساخته‌اید!\n\n ابتدا با دستور /make_config پیکربندی بسازید",
                reply_to_message_id=cmd.id
            )

        Info = await bot.get_chat(config['Target'])

        btn = [[
            InlineKeyboardButton(
                text='تغییر کانال هدف',
                callback_data='chgtarget'
            )
        ]]

        text = f"""
نام کانال: <code>{Info.title}</code>
نام کاربری کانال: <code>@{Info.username}</code>
شناسه کانال: <code>{Info.id}</code>
"""

        await cmd.reply_text(
            text=text,
            reply_to_message_id=cmd.id,
            reply_markup=InlineKeyboardMarkup(btn)
        )

    except Exception as e:
        print('خطا در خط {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)

# دستور حذف پیکربندی
@Client.on_message(filters.private & filters.user(Config.SUDO) & filters.command('del_config'))
async def delete_config(bot: Client, cmd: Message):
    btn = [
        [InlineKeyboardButton(text='بله', callback_data='delconfig-yes')],
        [InlineKeyboardButton(text='خیر', callback_data='delconfig-no')]
    ]

    await cmd.reply_text(
        text="**⚠️ آیا مطمئن هستید؟**\n\nآیا می‌خواهید پیکربندی را حذف کنید؟",
        reply_to_message_id=cmd.id,
        reply_markup=InlineKeyboardMarkup(btn)
    )
