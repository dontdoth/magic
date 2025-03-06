import json
import os
from pathlib import Path
import re
import subprocess
import sys
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from info import Config, Txt

# مسیر فایل پیکربندی
config_path = Path("config.json")

# دستور ساخت پیکربندی - فقط برای ادمین‌ها
@Client.on_message(filters.private & filters.chat(Config.SUDO) & filters.command('make_config'))
async def make_config(bot: Client, msg: Message):
    try:
        # بررسی وجود فایل پیکربندی
        if config_path.exists():
            return await msg.reply_text(
                text="**شما قبلاً یک پیکربندی ساخته‌اید. ابتدا آن را حذف کنید**\n\n از دستور /del_config استفاده کنید", 
                reply_to_message_id=msg.id
            )
        else:
            while True:
                try:
                    # دریافت تعداد اکانت‌ها
                    n = await bot.ask(
                        text=Txt.SEND_NUMBERS_MSG, 
                        chat_id=msg.chat.id,
                        filters=filters.text,
                        timeout=60
                    )
                except:
                    await bot.send_message(
                        msg.from_user.id,
                        "خطا!\n\nزمان درخواست تمام شد.\nبا استفاده از /make_config دوباره شروع کنید",
                        reply_to_message_id=n.id
                    )
                    return

                try:
                    # دریافت کانال هدف
                    target = await bot.ask(
                        text=Txt.SEND_TARGET_CHANNEL,
                        chat_id=msg.chat.id,
                        filters=filters.text,
                        timeout=60
                    )
                except:
                    await bot.send_message(
                        msg.from_user.id,
                        "خطا!\n\nزمان درخواست تمام شد.\nبا استفاده از /make_config دوباره شروع کنید",
                        reply_to_message_id=msg.id
                    )
                    return

                # بررسی صحت ورودی‌ها
                if str(n.text).isnumeric():
                    if not str(target.text).isnumeric():
                        break
                    else:
                        await msg.reply_text(
                            text="⚠️ **لطفاً لینک یا نام کاربری معتبر کانال هدف را وارد کنید!**",
                            reply_to_message_id=target.id
                        )
                        continue
                else:
                    await msg.reply_text(
                        text="⚠️ **لطفاً یک عدد صحیح وارد کنید!**",
                        reply_to_message_id=n.id
                    )
                    continue

            # پردازش آیدی کانال هدف
            group_target_id = target.text
            gi = re.sub("(@)|(https://)|(http://)|(t.me/)", "", group_target_id)

            # بررسی وجود کانال
            try:
                await bot.get_chat(gi)
            except Exception as e:
                return await msg.reply_text(
                    text=f"{e} \n\nخطا!",
                    reply_to_message_id=target.id
                )

            # ساخت دیکشنری پیکربندی
            config = {
                "Target": gi,
                "accounts": []
            }

            # دریافت سشن‌های اکانت‌ها
            for _ in range(int(n.text)):
                try:
                    session = await bot.ask(
                        text=Txt.SEND_SESSION_MSG,
                        chat_id=msg.chat.id,
                        filters=filters.text,
                        timeout=60
                    )
                except:
                    await bot.send_message(
                        msg.from_user.id,
                        "خطا!\n\nزمان درخواست تمام شد.\nبا استفاده از /make_config دوباره شروع کنید",
                        reply_to_message_id=msg.id
                    )
                    return

                # بررسی تکراری نبودن اکانت
                if config_path.exists():
                    for account in config['accounts']:
                        if account['Session_String'] == session.text:
                            return await msg.reply_text(
                                text=f"**اکانت {account['OwnerName']} قبلاً در پیکربندی وجود دارد**\n\nخطا!",
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
                        msg.chat.id,
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
                    return await msg.reply_text('**خطایی رخ داد! لطفاً ورودی‌های خود را بررسی کنید**')

                # افزودن اکانت به پیکربندی
                try:
                    new_account = {
                        "Session_String": session.text,
                        "OwnerUid": AccountHolder['id'],
                        "OwnerName": AccountHolder['first_name']
                    }
                    config["accounts"].append(new_account)

                    with open(config_path, 'w', encoding='utf-8') as file:
                        json.dump(config, file, indent=4)
                except Exception as e:
                    print(e)

            # نمایش دکمه‌های اکانت‌ها
            account_btn = [
                [InlineKeyboardButton(
                    text='اکانت‌های اضافه شده',
                    callback_data='account_config'
                )]
            ]
            
            await msg.reply_text(
                text=Txt.MAKE_CONFIG_DONE_MSG.format(n.text),
                reply_to_message_id=n.id,
                reply_markup=InlineKeyboardMarkup(account_btn)
            )

    except Exception as e:
        print('خطا در خط {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)

# دستور مشاهده اکانت‌ها
@Client.on_message(filters.private & filters.chat(Config.SUDO) & filters.command('see_accounts'))
async def see_account(bot: Client, msg: Message):
    try:
        config = (json.load(open("config.json")))['accounts']
        account_btn = [
            [InlineKeyboardButton(
                text='اکانت‌های اضافه شده',
                callback_data='account_config'
            )]
        ]
        
        await msg.reply_text(
            text=Txt.ADDED_ACCOUNT.format(len(config)),
            reply_to_message_id=msg.id,
            reply_markup=InlineKeyboardMarkup(account_btn)
        )

    except:
        return await msg.reply_text(
            text="**شما هیچ اکانتی اضافه نکرده‌اید 0️⃣**\n\nبرای افزودن اکانت از دستور /make_config استفاده کنید 👥",
            reply_to_message_id=msg.id
        )
