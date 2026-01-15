import random
import string

# def generate_voucher_code():
#     prefix = "SVA"
#     # Generate 12 random alphanumeric characters
#     random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
#     # Insert 'Q' at a random position to make it 13 characters long
#     insert_pos = random.randint(0, 12)
#     random_chars = random_chars[:insert_pos] + 'Q' + random_chars[insert_pos:]
#     return f"{prefix}{random_chars}"

# def generate_and_check_vouchers(num_to_generate, headers, verbose=True):
#     generated_vouchers = []
#     valid_generated_vouchers = []
#     if verbose:
#         print(f"\n✨ Generating and checking {num_to_generate} new vouchers... ✨")

#     for i in range(num_to_generate):
#         code = generate_voucher_code()
#         generated_vouchers.append({'code': code})
#         if verbose:
#             print(f"Generating and validating {i+1}/{num_to_generate} → {code}")
        
#         status_code, response_data = check_voucher(code, headers)
#         if status_code is None:
#             if verbose:
#                 print("❌ Validation failed for generated voucher. Skipping.")
#             continue

#         if is_voucher_applicable(response_data):
#             value = get_voucher_value(code) # Try to get value even for generated ones
#             if value:
#                 if verbose:
#                     print(f"✅ GENERATED & WORKING! → {code} worth ₹{value} 🎉")
#                 valid_generated_vouchers.append((code, value))
#             else:
#                 if verbose:
#                     print(f"✅ GENERATED & Applicable → {code} (value unknown)")
#                     valid_generated_vouchers.append((code, 0)) # Add with 0 value if unknown
#         else:
#             if verbose:
#                 print(f"❌ GENERATED & Not working → {code}")
#         reset_voucher(code, headers)
#         time.sleep(1) # Small delay between checks

#     if valid_generated_vouchers and verbose:
import json
import requests
import time
import re
import signal
import sys

VOUCHER_VALUES = {
    "SVA": 4000,
    "SVC": 1000,
    "SVD": 2000,
    "SVH": 500
}

def signal_handler(sig, frame):
    print("\n🔚 Terminating session gracefully...")
    sys.exit(0)

def load_cookies():
    with open("cookies.json", "r", encoding="utf-8") as f:
        raw = f.read().strip()
    try:
        # Try to parse the file content as JSON
        data = json.loads(raw)
        
        # Check if it's a list of cookie objects (common export format)
        if isinstance(data, list):
            cookies = []
            for cookie in data:
                if 'name' in cookie and 'value' in cookie:
                    cookies.append(f"{cookie['name']}={cookie['value']}")
            return "; ".join(cookies)
        
        # Check if it's a dictionary/object
        elif isinstance(data, dict):
            return "; ".join(f"{k}={v}" for k, v in data.items())
            
    except json.JSONDecodeError:
        # If it's not valid JSON, assume it's a raw cookie string
        pass
        
    # Return the raw string if JSON parsing fails or format is unexpected
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
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "x-tenant-id": "SHEIN",
        "cookie": cookie_string
    }

def get_voucher_value(code):
    prefix = code[:3].upper()
    return VOUCHER_VALUES.get(prefix, None)

def parse_vouchers_file():
    vouchers = []
    with open("vouchers.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("==="):
                continue
            vouchers.append({'code': line})
    return vouchers

def check_voucher(voucher_code, headers):
    url = "https://www.sheinindia.in/api/cart/apply-voucher"
    payload = {
        "voucherId": voucher_code,
        "device": {
            "client_type": "web"
        }
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        return response.status_code, response.json()
    except Exception as e:
        print(f"⚠️ Validation error for {voucher_code}: {str(e)}")
        return None, None

def reset_voucher(voucher_code, headers):
    url = "https://www.sheinindia.in/api/cart/reset-voucher"
    payload = {
        "voucherId": voucher_code,
        "device": {
            "client_type": "web"
        }
    }
    try:
        requests.post(url, json=payload, headers=headers, timeout=30)
    except Exception as e:
        print(f"⚠️ Reset error for {voucher_code}: {str(e)}")

def is_voucher_applicable(response_data):
    if not response_data:
        return False
    if "errorMessage" in response_data:
        errors = response_data.get("errorMessage", {}).get("errors", [])
        for error in errors:
            if error.get("type") == "VoucherOperationError":
                if "not applicable" in error.get("message", "").lower():
                    return False
    return "errorMessage" not in response_data

def run_check(verbose=True):
    if verbose:
        print(f"\n🚀 Commencing voucher scan at {time.strftime('%Y-%m-%d %H:%M:%S')} 🚀")
        print("🔑 Retrieving session data...")
    cookie_string = load_cookies()
    headers = get_headers(cookie_string)
    if verbose:
        print("📜 Analyzing voucher list...")
    vouchers = parse_vouchers_file()
    if verbose:
        print(f"🔍 Detected {len(vouchers)} codes to validate")
    if len(vouchers) == 0:
        if verbose:
            print("📭 No vouchers found. Skipping this cycle.")
        return [], []
    valid_vouchers = []
    checked_count = 0
    for i, voucher in enumerate(vouchers, 1):
        code = voucher['code']
        value = get_voucher_value(code)
        if verbose:
            print(f"Validating {i}/{len(vouchers)} → {code}")
        status_code, response_data = check_voucher(code, headers)
        checked_count += 1
        if status_code is None:
            if verbose:
                print("❌ Validation failed , Please try again or Check Manually")
            continue
        if is_voucher_applicable(response_data):
            if value:
                if verbose:
                    print(f"✅ WORKING! → {code} worth ₹{value} 🎉")
                valid_vouchers.append((code, value))
            else:
                if verbose:
                    print(f"✅ Applicable → {code} (value unknown)")
        else:
            if verbose:
                print(f"❌ Not working → {code}")
        reset_voucher(code, headers)
        time.sleep(1)
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    if valid_vouchers and verbose:
        with open("valid_vouchers.txt", "a", encoding="utf-8") as f:
            f.write(f"\n🎯 Valid Vouchers Found - {timestamp} 🎯\n")
            grouped = {}
            for code, val in valid_vouchers:
                grouped.setdefault(val, []).append(code)
            for val in sorted(grouped.keys(), reverse=True):
                f.write(f"\n💸 Worth ₹{val} 💸\n")
                for code in grouped[val]:
                    f.write(f"{code}\n")
        total_saved = sum(val for _, val in valid_vouchers)
        print(f"\n🎉 SUCCESS! Found {len(valid_vouchers)} valid vouchers worth ₹{total_saved} in total! 🎉")
        print("💾 Saved to 'valid_vouchers.txt'")
    elif verbose:
        print("\n😔 No valid vouchers with known value found this time.")
    return valid_vouchers, checked_count

def main():
    print(r"""
========================================================
██╗   ██╗███████╗███╗   ██╗ ██████╗ ███╗   ███╗
██║   ██║██╔════╝████╗  ██║██╔═══██╗████╗ ████║
██║   ██║█████╗  ██╔██╗ ██║██║   ██║██╔████╔██║
╚██╗ ██╔╝██╔══╝  ██║╚██╗██║██║   ██║██║╚██╔╝██║
 ╚████╔╝ ███████╗██║ ╚████║╚██████╔╝██║ ╚═╝ ██║
  ╚═══╝  ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝

          Made By @HeyVenomBro
    Join @ScripterUltraProMax & @SheinXCodes
========================================================
""")
    signal.signal(signal.SIGINT, signal_handler)
    print("🛡️  SHEIN Voucher Checker + Protector 🛡️")
    print("Initiating first full scan...\n")

    valid_found, _ = run_check(verbose=True)

    print("\n🔄 Would you like to enable Protection Mode? (y/n): ")
    choice = input().strip().lower()
    if choice == 'y':
        print("\n🛡️ Protection Mode ON! 🛡️")
        print("🔍 Auto-scanning every 10 minutes to secure your vouchers...\n")
        time.sleep(5)
        check_num = 1
        while True:
            try:
                valid_found, checked = run_check(verbose=False)
                if valid_found:
                    total_val = sum(val for _, val in valid_found)
                    print(f"✅ Cycle #{check_num} → {len(valid_found)} valid vouchers worth ₹{total_val} secured! 💰")
                else:
                    print(f"⏳ Cycle #{check_num} completed → No new valid vouchers ({checked} checked)")
                check_num += 1
                print("😴 Sleeping 10 minutes before next scan...\n")
                time.sleep(600)
            except KeyboardInterrupt:
                print("\n👋 Protection mode stopped by user.")
                break
            except Exception as e:
                print(f"⚠️ Error occurred: {str(e)}. Retrying in 10 minutes...")
                time.sleep(600)
    else:
        print("👋 Session ended. Happy shopping!")

if __name__ == "__main__":
    main()
