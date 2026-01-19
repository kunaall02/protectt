import random
import string
import json
import requests
import time
import re
import signal
import sys
import os
os.environ["TZ"] = "UTC"
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

VOUCHER_VALUES = {
    "SVA": 4000,
    "SVC": 1000,
    "SVD": 2000,
    "SVH": 500
}

TELEGRAM_BOT_TOKEN = "8409968687:AAF2brzjPQfi4fQW9TpvGPjg5d7ca1rGXeI"
TELEGRAM_CHAT_ID = "7243538468"

last_scan_report = None


def signal_handler(sig, frame):
    print("\n🔚 Terminating session gracefully...")
    sys.exit(0)


def load_cookies():
    with open("cookies.json", "r", encoding="utf-8") as f:
        raw = f.read().strip()
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return "; ".join(f"{c['name']}={c['value']}" for c in data if 'name' in c)
        elif isinstance(data, dict):
            return "; ".join(f"{k}={v}" for k, v in data.items())
    except json.JSONDecodeError:
        pass
    return raw


def get_headers(cookie_string):
    return {
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "origin": "https://www.sheinindia.in",
        "pragma": "no-cache",
        "referer": "https://www.sheinindia.in/cart",
        "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "x-tenant-id": "SHEIN",
        "cookie": cookie_string
    }


def get_voucher_value(code):
    return VOUCHER_VALUES.get(code[:3].upper(), None)


def parse_vouchers_file():
    with open("vouchers.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def check_voucher(voucher_code, headers):
    url = "https://www.sheinindia.in/api/cart/apply-voucher"
    payload = {"voucherId": voucher_code, "device": {"client_type": "web"}}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        return r.status_code, r.json()
    except Exception:
        return None, None


def reset_voucher(voucher_code, headers):
    url = "https://www.sheinindia.in/api/cart/reset-voucher"
    payload = {"voucherId": voucher_code, "device": {"client_type": "web"}}
    try:
        requests.post(url, json=payload, headers=headers, timeout=30)
    except Exception:
        pass


def is_voucher_applicable(response_data):
    return response_data and "errorMessage" not in response_data


def run_check(verbose=True):
    global last_scan_report
    cookie_string = load_cookies()
    headers = get_headers(cookie_string)
    vouchers = parse_vouchers_file()

    valid = []
    for code in vouchers:
        status, data = check_voucher(code, headers)
        if status and is_voucher_applicable(data):
            val = get_voucher_value(code)
            valid.append((code, val))
        reset_voucher(code, headers)
        time.sleep(1)

    if valid:
        report = "\n".join(f"{c} ₹{v}" for c, v in valid)
        last_scan_report = report
        with open("valid_vouchers.txt", "a") as f:
            f.write(report + "\n")

    return valid


def start_command(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Bot started. Use /status to see last scan."
    )


def status_command(update, context):
    if last_scan_report:
        context.bot.send_message(update.effective_chat.id, last_scan_report)
    else:
        context.bot.send_message(update.effective_chat.id, "No scan data yet.")


def main():
    signal.signal(signal.SIGINT, signal_handler)

    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CommandHandler("status", status_command))

    updater.start_polling(drop_pending_updates=True)

    import threading
    threading.Thread(
        target=run_check,
        kwargs={"verbose": False},
        daemon=True
    ).start()

    updater.idle()   # ❗❗ YEH LINE SABSE IMPORTANT HAI


if __name__ == "__main__":
    main()
