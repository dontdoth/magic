import sys
import json
import asyncio
from typing import Optional
from pyrogram import Client
from pyrogram.raw.functions.account import ReportPeer
from pyrogram.raw.types import (
    InputReportReasonChildAbuse,
    InputReportReasonFake,
    InputReportReasonCopyright,
    InputReportReasonGeoIrrelevant,
    InputReportReasonPornography,
    InputReportReasonIllegalDrugs,
    InputReportReasonSpam,
    InputReportReasonPersonalDetails,
    InputReportReasonViolence,
    InputPeerChannel
)

# تعریف دلایل گزارش
REPORT_REASONS = {
    "Report for child abuse": InputReportReasonChildAbuse,
    "Report for impersonation": InputReportReasonFake,
    "Report for copyrighted content": InputReportReasonCopyright,
    "Report an irrelevant geogroup": InputReportReasonGeoIrrelevant,
    "Reason for Pornography": InputReportReasonPornography,
    "Report an illegal durg": InputReportReasonIllegalDrugs,
    "Report for offensive person detail": InputReportReasonSpam,
    "Report for spam": InputReportReasonPersonalDetails,
    "Report for Violence": InputReportReasonViolence
}

def get_report_reason(reason_text: str) -> Optional[object]:
    """دریافت نوع گزارش بر اساس متن"""
    reason_class = REPORT_REASONS.get(reason_text)
    return reason_class() if reason_class else None

async def report_channel(
    app: Client,
    channel_username: str,
    reason_obj: object,
    reason_text: str,
    account_name: str
) -> bool:
    """ارسال گزارش برای یک کانال"""
    try:
        # دریافت اطلاعات کانال
        peer = await app.resolve_peer(channel_username)
        channel = InputPeerChannel(
            channel_id=peer.channel_id,
            access_hash=peer.access_hash
        )

        # ساخت و ارسال گزارش
        report = ReportPeer(
            peer=channel,
            reason=reason_obj,
            message=reason_text
        )
        result = await app.invoke(report)

        print(f"✅ گزارش توسط اکانت {account_name} با موفقیت ارسال شد")
        return True

    except Exception as e:
        print(f"❌ خطا در ارسال گزارش از اکانت {account_name}:")
        print(f"علت: {str(e)}")
        return False

async def main(reason_text: str):
    """تابع اصلی برنامه"""
    try:
        # خواندن پیکربندی
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)

        # دریافت نوع گزارش
        reason_obj = get_report_reason(reason_text)
        if not reason_obj:
            print("❌ دلیل گزارش نامعتبر است")
            return

        # ارسال گزارش با همه اکانت‌ها
        target = config['Target']
        success_count = 0
        
        for account in config["accounts"]:
            session = account["Session_String"]
            name = account['OwnerName']

            async with Client(
                name="Session",
                session_string=session
            ) as app:
                if await report_channel(
                    app,
                    target,
                    reason_obj,
                    reason_text,
                    name
                ):
                    success_count += 1

        # نمایش نتیجه
        total = len(config["accounts"])
        print(f"\n📊 نتیجه گزارش‌ها:")
        print(f"✅ موفق: {success_count}")
        print(f"❌ ناموفق: {total - success_count}")
        print(f"📱 کل اکانت‌ها: {total}")

    except FileNotFoundError:
        print("❌ فایل پیکربندی (config.json) یافت نشد")
    except json.JSONDecodeError:
        print("❌ خطا در خواندن فایل پیکربندی")
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {str(e)}")

if __name__ == "__main__":
    # بررسی پارامترهای ورودی
    if len(sys.argv) != 2:
        print("❌ استفاده صحیح:")
        print("python script.py <reason>")
        sys.exit(1)

    # اجرای برنامه
    input_reason = sys.argv[1]
    asyncio.run(main(input_reason))
