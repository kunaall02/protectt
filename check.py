from curl_cffi import requests
import time

url = "https://www.sheinindia.in/api/cart/apply-voucher"

def load_cookies():
    cookies = {}
    try:
        with open("cookies.txt", "r", encoding="utf-8") as f:
            for part in f.read().split(";"):
                part = part.strip()
                if "=" in part:
                    k, v = part.split("=", 1)
                    cookies[k.strip()] = v.strip()
    except Exception as e:
        print("Cookie load error:", e)
    return cookies

def load_codes():
    with open("code.txt", "r", encoding="utf-8") as f:
        return [c.strip() for c in f if c.strip()]

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "user-agent": "Mozilla/5.0 (Linux; Android 10; K)",
    "x-tenant-id": "SHEIN",
}

# curl-cffi session
session = requests.Session()
IMPERSONATE = "chrome120"

print("Starting voucher auto-check (every 7 minutes)...\n")

while True:
    print("Running check cycle...\n")

    cookies = load_cookies()   # reload in case updated
    codes = load_codes()

    for code in codes:
        data = {
            "voucherId": code,
            "device": {"client_type": "MSITE"}
        }

        try:
            r = session.post(
                url,
                json=data,
                headers=headers,
                cookies=cookies,
                impersonate=IMPERSONATE,
                timeout=30,
            )

            try:
                resp = r.json()
                msg = (
                    resp.get("errorMessage", {})
                        .get("errors", [{}])[0]
                        .get("message", "No message")
                )
                print(f"{code} => {msg}")
            except Exception:
                print(f"{code} => RAW RESPONSE:", r.text)

        except Exception as e:
            print(f"{code} => REQUEST ERROR:", e)

        time.sleep(2)  # small delay between codes (prevents rate limit)

    print("\nWaiting 7 minutes before next recheck...\n")
    time.sleep(420)  # 7 minutes (7 × 60)
