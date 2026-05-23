import telebot
from telebot.types import *
import requests
import sqlite3
import json
import time
import re
from datetime import datetime

# ============ APNA BOT TOKEN YAHAN DALO ============
BOT_TOKEN = "8717813336:AAHhZP_AFg4icVwdA1n2wCQd0YpVlpSLVvs"  # CHANGE THIS!

MAIN_GROUP = "@aghunter"

CHANNELS = [
    "@aghunter",
    "@nibhadarling",
    "@infobotfreet"
]

ADMIN_ID = 8643031554
ADMIN_USERNAME = "@SYKO_KILLER"

UPI_ID = "9939738510@fam"

# ============ DATABASE SETUP ============
conn = sqlite3.connect("db.sqlite", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    credits INTEGER DEFAULT 15,
    verified INTEGER DEFAULT 0
)
""")
conn.commit()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN verified INTEGER DEFAULT 0")
    conn.commit()
except:
    pass

print("✅ Database ready")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
user_verified_cache = {}

def get_user(uid, username=""):
    try:
        cursor.execute("SELECT credits, verified FROM users WHERE user_id=?", (uid,))
        data = cursor.fetchone()

        if not data:
            verified_status = 1 if is_admin(uid) else 0
            cursor.execute("INSERT INTO users (user_id, username, credits, verified) VALUES (?,?,?,?)", 
                         (uid, username, 15, verified_status))
            conn.commit()
            user_verified_cache[uid] = bool(verified_status)
            
            # Send welcome notification for new user
            if not is_admin(uid):
                send_welcome_notification(uid, username)
            
            return 15, bool(verified_status)

        cursor.execute("UPDATE users SET username=? WHERE user_id=?", (username, uid))
        conn.commit()
        
        verified = bool(data[1])
        user_verified_cache[uid] = verified
        return data[0], verified
    except:
        return 15, False

def set_user(uid, credits):
    cursor.execute("UPDATE users SET credits=? WHERE user_id=?", (credits, uid))
    conn.commit()

def set_verified(uid, status):
    cursor.execute("UPDATE users SET verified=? WHERE user_id=?", (1 if status else 0, uid))
    conn.commit()
    user_verified_cache[uid] = status

def is_admin(uid):
    return uid == ADMIN_ID

def check_verification(uid):
    if is_admin(uid):
        return True
    if uid in user_verified_cache:
        return user_verified_cache[uid]
    _, verified = get_user(uid, "")
    return verified

def check_credits(uid, chat_type):
    """Check credits - Group mein unlimited, Private mein credits check"""
    if chat_type != "private":
        return True, -1
    
    bal, _ = get_user(uid, "")
    if bal <= 0:
        return False, bal
    return True, bal

# ============ STYLISH NOTIFICATION FUNCTION ============
def send_welcome_notification(uid, username):
    """Send stylish welcome notification to admin"""
    
    current_time = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
    
    notification = f"""
╔════════════════════════════════════════╗
║     🎉 <b>NEW USER ALERT</b> 🎉            ║
╚════════════════════════════════════════╝

<b>✨ USER DETAILS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>🆔 User ID:</b> <code>{uid}</code>
<b>👤 Username:</b> @{username if username else 'No Username'}
<b>💎 Credits:</b> <b>15 FREE Credits</b>
<b>📅 Joined:</b> {current_time}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>💰 Total Users:</b> {get_total_users()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👨‍💻 <b>@Gautamxlive</b>
"""
    
    try:
        bot.send_message(ADMIN_ID, notification, parse_mode="HTML")
    except:
        pass

def get_total_users():
    """Get total number of users"""
    cursor.execute("SELECT COUNT(*) FROM users")
    return cursor.fetchone()[0]

def send_credit_usage_notification(uid, username, service, remaining_credits):
    """Send notification when user uses credits"""
    
    current_time = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
    
    notification = f"""
╔════════════════════════════════════════╗
║     ⚡ <b>CREDIT USED</b> ⚡               ║
╚════════════════════════════════════════╝

<b>👤 USER</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>🆔 ID:</b> <code>{uid}</code>
<b>📛 Username:</b> @{username if username else 'No Username'}

<b>🔍 SERVICE USED</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>📱 Service:</b> {service}
<b>💎 Credits Used:</b> <b>1</b>
<b>💰 Remaining:</b> <b>{remaining_credits}</b>
<b>📅 Time:</b> {current_time}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👨‍💻 <b>@Gautamxlive</b>
"""
    
    try:
        bot.send_message(ADMIN_ID, notification, parse_mode="HTML")
    except:
        pass

def send_low_credit_notification(uid, username, credits):
    """Send notification when credits are low"""
    
    if credits <= 3:
        notification = f"""
╔════════════════════════════════════════╗
║     ⚠️ <b>LOW CREDIT ALERT</b> ⚠️          ║
╚════════════════════════════════════════╝

<b>👤 USER</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>🆔 ID:</b> <code>{uid}</code>
<b>📛 Username:</b> @{username if username else 'No Username'}

<b>💰 CREDIT STATUS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>⚠️ Credits Left:</b> <b>{credits}</b>
<b>📉 Status:</b> <b>CRITICAL</b>

<b>💡 Suggest user to recharge!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👨‍💻 <b>@Gautamxlive</b>
"""
        try:
            bot.send_message(ADMIN_ID, notification, parse_mode="HTML")
        except:
            pass

def join_kb():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🔗 JOIN CHANNEL 1", url="https://t.me/aghunter"))
    kb.add(InlineKeyboardButton("🔗 JOIN CHANNEL 2", url="https://t.me/nibhadarling"))
    kb.add(InlineKeyboardButton("🔗 JOIN CHANNEL 3", url="https://t.me/infobotfreet"))
    kb.add(InlineKeyboardButton("✅ VERIFY", callback_data="verify_channels"))
    return kb

@bot.callback_query_handler(func=lambda call: call.data == "verify_channels")
def verify_callback(call):
    uid = call.from_user.id
    
    if check_verification(uid):
        bot.answer_callback_query(call.id, "✅ Already verified!", show_alert=True)
        return
    
    all_joined = True
    for ch in CHANNELS:
        try:
            member = bot.get_chat_member(ch, uid)
            status = str(member.status).lower()
            if status not in ["member", "administrator", "creator"]:
                all_joined = False
                break
        except:
            all_joined = False
            break
    
    if all_joined:
        set_verified(uid, True)
        bot.answer_callback_query(call.id, "✅ Verified! Send /start again", show_alert=True)
        try:
            bot.edit_message_text(
                "✅ **VERIFIED!**\n\nSend /start to use the bot",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown"
            )
        except:
            pass
    else:
        bot.answer_callback_query(call.id, "❌ Join ALL channels first!", show_alert=True)

# ============ KEYBOARD BUTTONS ONLY FOR PRIVATE ============
def private_menu():
    """Keyboard buttons for private chat only"""
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=2
    )
    kb.add(
        KeyboardButton("📱 Num Info"),
        KeyboardButton("👤 Num To Name")
    )
    kb.add(
        KeyboardButton("👨‍👩‍👦 Family Info"),
        KeyboardButton("💎 TG To Num")
    )
    kb.add(
        KeyboardButton("🔄 TG User To Number"),
        KeyboardButton("🚘 Vehicle Info")
    )
    kb.add(
        KeyboardButton("💰 Buy Credits"),
        KeyboardButton("👤 My Account")
    )
    return kb

def remove_keyboard():
    """Remove keyboard"""
    return ReplyKeyboardRemove()

def send_welcome_message(chat_id, first_name, user_id, chat_type):
    """Send welcome message with appropriate keyboard"""
    
    if chat_type == "private":
        # Private chat - full keyboard
        bal, _ = get_user(user_id, "")
        welcome_msg = f"""
╔════════════════════════════════════════╗
║     ✨ <b>WELCOME TO GAUTAM X BOT</b> ✨    ║
╚════════════════════════════════════════╝

<b>👋 Hello {first_name}!</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>💰 ACCOUNT DETAILS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>💎 Credits:</b> <b>{bal} FREE Credits</b>
<b>⚡ Per Search:</b> 1 Credit

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>🔍 AVAILABLE SERVICES</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 Num Info
👤 Num to Name
👨‍👩‍👦 Family Info
💎 TG to Num
🔄 TG User to Number
🚘 Vehicle Info

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 <b>Click any button below to start</b>
💰 <b>Buy Credits</b> for more searches
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👨‍💻 <b>@Gautamxlive</b>
"""
        bot.send_message(chat_id, welcome_msg, reply_markup=private_menu(), parse_mode="HTML")
    else:
        # Group chat - NO keyboard, only commands
        welcome_msg = f"""
╔════════════════════════════════════════╗
║     🎉 <b>GAUTAM X INFO BOT</b> 🎉         ║
╚════════════════════════════════════════╝

<b>👋 Hello {first_name}!</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>🎯 GROUP MODE - UNLIMITED FREE</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>📱 Commands:</b>
• /num [number] - Num Info
• /name [number] - Num to Name
• /family [aadhar] - Family Info
• /tg [username] - TG to Num
• /tgid [userid] - TG User to Num
• /vehicle [number] - Vehicle Info

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 <b>Use commands directly in group</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👨‍💻 <b>@Gautamxlive</b>
"""
        bot.send_message(chat_id, welcome_msg, parse_mode="HTML")

def loading(chat_id):
    return bot.send_message(chat_id, "⏳ <b>Processing...</b>", parse_mode="HTML")

def format_json_only(data, query_type, query_value):
    separator = "─" * 45
    service_names = {
        "phone": "📱 NUM INFO",
        "name": "👤 NUM TO NAME",
        "aadhar": "👨‍👩‍👦 FAMILY INFO",
        "vehicle": "🚘 VEHICLE INFO",
        "tguser": "💎 TG TO NUM",
        "tg": "🔄 TG USER TO NUM"
    }
    service_name = service_names.get(query_type, "📊 INFO")
    
    if isinstance(data, dict):
        data["developer"] = "@Gautamxlive"
    
    json_output = json.dumps(data, indent=2, ensure_ascii=False)
    
    if len(json_output) > 3000:
        json_output = json_output[:3000] + "\n... (truncated)"
    
    return f"""
<b>{service_name}</b>
{separator}
<b>📊 Data Fetched</b> : ✅

<b>📋 INPUT</b>
<code>{query_value}</code>

<b>📄 JSON OUTPUT</b>
<code>{json_output}</code>
{separator}
👨‍💻 <b>@Gautamxlite</b>
"""

def extract_numbers_from_json(data):
    numbers = []
    def extract_recursive(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str):
                    if re.match(r'^\+?\d{10,13}$', value) and len(re.sub(r'\D', '', value)) >= 10:
                        clean_num = re.sub(r'\D', '', value)
                        if clean_num not in numbers:
                            numbers.append(clean_num)
                else:
                    extract_recursive(value)
        elif isinstance(obj, list):
            for item in obj:
                extract_recursive(item)
    extract_recursive(data)
    return numbers

def stylish_recharge_message():
    return f"""
╔════════════════════════════════════════╗
║     💰 <b>RECHARGE YOUR CREDITS</b> 💰     ║
╚════════════════════════════════════════╝

<b>✨ PREMIUM PLANS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>🎯 10 Credits</b> → <b>₹50</b>
<b>🚀 20 Credits</b> → <b>₹90</b>
<b>💎 50 Credits</b> → <b>₹200</b>
<b>👑 100 Credits</b> → <b>₹350</b> (BEST VALUE)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>💳 PAYMENT DETAILS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>UPI ID:</b> <code>{UPI_ID}</code>
<b>PayTM:</b> <code>9939738510</code>
<b>PhonePe:</b> <code>9939738510</code>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>📌 HOW TO RECHARGE?</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1️⃣ <b>Send Payment</b> to above UPI ID
2️⃣ <b>Take Screenshot</b>
3️⃣ <b>Forward to</b> @SYKO_KILLER

<b>⚡ Credits added within 2-5 minutes</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👨‍💻 <b>@SYKO_KILLER</b>
"""

def stylish_recharge_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("🎯 ₹50 - 10 Credits", callback_data="plan_10"))
    kb.add(InlineKeyboardButton("🚀 ₹90 - 20 Credits", callback_data="plan_20"))
    kb.add(InlineKeyboardButton("💎 ₹200 - 50 Credits", callback_data="plan_50"))
    kb.add(InlineKeyboardButton("👑 ₹350 - 100 Credits", callback_data="plan_100"))
    kb.add(InlineKeyboardButton("👨‍💻 CONTACT ADMIN", url="https://t.me/SYKO_KILLER"))
    kb.add(InlineKeyboardButton("✅ CHECK BALANCE", callback_data="check_balance"))
    return kb

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "check_balance":
        bal, _ = get_user(call.from_user.id, call.from_user.username)
        
        balance_msg = f"""
╔════════════════════════════════════════╗
║     💎 <b>YOUR BALANCE</b> 💎             ║
╚════════════════════════════════════════╝

<b>💰 Credits:</b> <b>{bal}</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 <b>Need more credits?</b>
Click on <b>Buy Credits</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👨‍💻 <b>@Gautamxlive</b>
"""
        bot.answer_callback_query(call.id, f"💰 Balance: {bal} Credits", show_alert=True)
        bot.send_message(call.message.chat.id, balance_msg, parse_mode="HTML")
        
    elif call.data.startswith("copy_"):
        number = call.data.split("_")[1]
        bot.answer_callback_query(call.id, f"✅ Copied: {number}", show_alert=True)
        bot.send_message(call.message.chat.id, f"📋 <code>{number}</code>\n\n✅ Number copied to clipboard!", parse_mode="HTML")
        
    elif call.data.startswith("plan_"):
        plan = call.data.split("_")[1]
        plans = {"10": {"price": "50", "credits": "10"}, "20": {"price": "90", "credits": "20"}, 
                 "50": {"price": "200", "credits": "50"}, "100": {"price": "350", "credits": "100"}}
        if plan in plans:
            p = plans[plan]
            msg = f"""
╔════════════════════════════════════════╗
║     ✅ <b>PLAN SELECTED</b> ✅             ║
╚════════════════════════════════════════╝

<b>🎯 Plan:</b> {p['credits']} Credits
<b>💰 Amount:</b> ₹{p['price']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>💳 Send payment to:</b>
<code>{UPI_ID}</code>

<b>📸 After payment send screenshot to:</b>
@SYKO_KILLER

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ <b>Credits added after verification</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👨‍💻 <b>@SYKO_KILLER</b>
"""
            bot.send_message(call.message.chat.id, msg, parse_mode="HTML")
            bot.answer_callback_query(call.id, f"Selected {p['credits']} Credits Plan")

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    chat_id = m.chat.id
    chat_type = m.chat.type
    
    get_user(uid, m.from_user.username)
    
    if not check_verification(uid):
        bot.send_message(
            chat_id,
            """⚠️ **VERIFICATION REQUIRED** ⚠️

Please join all channels below and click **VERIFY**:

🔹 Join all 3 channels
🔹 Click VERIFY button
🔹 Then use the bot

""",
            reply_markup=join_kb(),
            parse_mode="Markdown"
        )
        return
    
    send_welcome_message(chat_id, m.from_user.first_name, uid, chat_type)

@bot.message_handler(commands=['services'])
def services(m):
    if not check_verification(m.from_user.id):
        start(m)
        return
    
    if m.chat.type == "private":
        bot.send_message(m.chat.id, "<b>🔎 Select Service</b>", reply_markup=private_menu(), parse_mode="HTML")
    else:
        # Group mein services command se sirf message
        bot.send_message(m.chat.id, """
<b>🔎 AVAILABLE COMMANDS</b>
─────────────────────────────────────────
📱 <code>/num 9876543210</code>
👤 <code>/name 9876543210</code>
👨‍👩‍👦 <code>/family 400204118594</code>
💎 <code>/tg @username</code>
🔄 <code>/tgid 123456789</code>
🚘 <code>/vehicle MP16CB6745</code>
─────────────────────────────────────────
🎉 <b>UNLIMITED FREE USE</b>
""", parse_mode="HTML")

@bot.message_handler(commands=['contact'])
def contact(m):
    if not check_verification(m.from_user.id):
        start(m)
        return
        
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("👨‍💻 ADMIN", url="https://t.me/SYKO_KILLER"))
    kb.add(InlineKeyboardButton("📢 GROUP", url="https://t.me/aghunter"))
    
    bot.send_message(m.chat.id, """
╔════════════════════════════════════════╗
║     📞 <b>CONTACT ADMIN</b> 📞            ║
╚════════════════════════════════════════╝

<b>👨‍💻 Admin:</b> @SYKO_KILLER
<b>⏰ Response:</b> Within 5 minutes
<b>💼 For:</b> Deals, Promotions, Support, Recharge

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 <b>Click below to contact</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""", reply_markup=kb, parse_mode="HTML")

@bot.message_handler(commands=['help'])
def cmd_help(m):
    if not check_verification(m.from_user.id):
        start(m)
        return
        
    chat_type = m.chat.type
    
    if chat_type != "private":
        txt = """
╔════════════════════════════════════════╗
║     🔥 <b>GROUP COMMANDS</b> 🔥           ║
╚════════════════════════════════════════╝

<b>📱 NUM INFO</b>
<code>/num 9876543210</code>

<b>👤 NUM TO NAME</b>
<code>/name 9876543210</code>

<b>👨‍👩‍👦 FAMILY INFO</b>
<code>/family 400204118594</code>

<b>💎 TG TO NUM</b>
<code>/tg @username</code>

<b>🔄 TG USER TO NUM</b>
<code>/tgid 123456789</code>

<b>🚘 VEHICLE INFO</b>
<code>/vehicle MP16CB6745</code>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 <b>UNLIMITED FREE FOR GROUP</b> 🎉
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👨‍💻 <b>@Gautamxlive</b>
"""
        bot.send_message(m.chat.id, txt, parse_mode="HTML")
    else:
        bal, _ = get_user(m.from_user.id, m.from_user.username)
        txt = f"""
╔════════════════════════════════════════╗
║     🔥 <b>PRIVATE COMMANDS</b> 🔥         ║
╚════════════════════════════════════════╝

<b>💰 Balance:</b> {bal} Credits
<b>⚡ Cost:</b> 1 Credit per search

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>📱 NUM INFO</b>
<code>/num 9876543210</code>

<b>👤 NUM TO NAME</b>
<code>/name 9876543210</code>

<b>👨‍👩‍👦 FAMILY INFO</b>
<code>/family 400204118594</code>

<b>💎 TG TO NUM</b>
<code>/tg @username</code>

<b>🔄 TG USER TO NUM</b>
<code>/tgid 123456789</code>

<b>🚘 VEHICLE INFO</b>
<code>/vehicle MP16CB6745</code>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 <b>Buy Credits</b> - Click button below
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👨‍💻 <b>@Gautamxlive</b>
"""
        bot.send_message(m.chat.id, txt, reply_markup=private_menu(), parse_mode="HTML")

@bot.message_handler(commands=['num'])
def cmd_num(m):
    uid = m.from_user.id
    chat_type = m.chat.type
    
    if not check_verification(uid):
        start(m)
        return
    
    can_proceed, bal = check_credits(uid, chat_type)
    if not can_proceed and chat_type == "private":
        bot.reply_to(m, "❌ <b>Insufficient Credits!</b>\n\nUse /buy or click Buy Credits button to recharge.", parse_mode="HTML")
        return
    
    try:
        value = m.text.split()[1]
        if not re.match(r'^\d{10}$', value):
            bot.reply_to(m, "❌ Invalid! Enter 10 digits")
            return
        process(m, "phone", value, chat_type)
    except IndexError:
        bot.reply_to(m, "❌ Usage: /num 9876543210")

@bot.message_handler(commands=['name'])
def cmd_name(m):
    uid = m.from_user.id
    chat_type = m.chat.type
    
    if not check_verification(uid):
        start(m)
        return
    
    can_proceed, bal = check_credits(uid, chat_type)
    if not can_proceed and chat_type == "private":
        bot.reply_to(m, "❌ <b>Insufficient Credits!</b>\n\nUse /buy or click Buy Credits button to recharge.", parse_mode="HTML")
        return
    
    try:
        value = m.text.split()[1]
        if not re.match(r'^\d{10}$', value):
            bot.reply_to(m, "❌ Invalid! Enter 10 digits")
            return
        process(m, "name", value, chat_type)
    except IndexError:
        bot.reply_to(m, "❌ Usage: /name 9876543210")

@bot.message_handler(commands=['family'])
def cmd_family(m):
    uid = m.from_user.id
    chat_type = m.chat.type
    
    if not check_verification(uid):
        start(m)
        return
    
    can_proceed, bal = check_credits(uid, chat_type)
    if not can_proceed and chat_type == "private":
        bot.reply_to(m, "❌ <b>Insufficient Credits!</b>\n\nUse /buy or click Buy Credits button to recharge.", parse_mode="HTML")
        return
    
    try:
        value = m.text.split()[1]
        process(m, "aadhar", value, chat_type)
    except IndexError:
        bot.reply_to(m, "❌ Usage: /family 400204118594")

@bot.message_handler(commands=['tg'])
def cmd_tg(m):
    uid = m.from_user.id
    chat_type = m.chat.type
    
    if not check_verification(uid):
        start(m)
        return
    
    can_proceed, bal = check_credits(uid, chat_type)
    if not can_proceed and chat_type == "private":
        bot.reply_to(m, "❌ <b>Insufficient Credits!</b>\n\nUse /buy or click Buy Credits button to recharge.", parse_mode="HTML")
        return
    
    try:
        value = m.text.split()[1]
        process(m, "tguser", value, chat_type)
    except IndexError:
        bot.reply_to(m, "❌ Usage: /tg @username")

@bot.message_handler(commands=['tgid'])
def cmd_tgid(m):
    uid = m.from_user.id
    chat_type = m.chat.type
    
    if not check_verification(uid):
        start(m)
        return
    
    can_proceed, bal = check_credits(uid, chat_type)
    if not can_proceed and chat_type == "private":
        bot.reply_to(m, "❌ <b>Insufficient Credits!</b>\n\nUse /buy or click Buy Credits button to recharge.", parse_mode="HTML")
        return
    
    try:
        value = m.text.split()[1]
        process(m, "tg", value, chat_type)
    except IndexError:
        bot.reply_to(m, "❌ Usage: /tgid 123456789")

@bot.message_handler(commands=['vehicle'])
def cmd_vehicle(m):
    uid = m.from_user.id
    chat_type = m.chat.type
    
    if not check_verification(uid):
        start(m)
        return
    
    can_proceed, bal = check_credits(uid, chat_type)
    if not can_proceed and chat_type == "private":
        bot.reply_to(m, "❌ <b>Insufficient Credits!</b>\n\nUse /buy or click Buy Credits button to recharge.", parse_mode="HTML")
        return
    
    try:
        value = m.text.split()[1]
        process(m, "vehicle", value.upper(), chat_type)
    except IndexError:
        bot.reply_to(m, "❌ Usage: /vehicle MP16CB6745")

@bot.message_handler(commands=['buy'])
def buy_cmd(m):
    if m.chat.type != "private":
        bot.reply_to(m, "❌ Use this command in private chat only!\nContact @SYKO_KILLER for recharge")
        return
    
    if not check_verification(m.from_user.id):
        start(m)
        return
    
    bot.send_message(m.chat.id, stylish_recharge_message(), reply_markup=stylish_recharge_keyboard(), parse_mode="HTML")

@bot.message_handler(commands=['add'])
def add_credit(m):
    if m.chat.type != "private":
        return
    if not is_admin(m.from_user.id):
        return
    try:
        args = m.text.split()
        target = args[1]
        amount = int(args[2])
        if target.startswith("@"):
            username = target.replace("@", "").lower()
            cursor.execute("SELECT user_id,credits FROM users WHERE lower(username)=?", (username,))
            data = cursor.fetchone()
            if not data:
                bot.reply_to(m, "❌ Username not found")
                return
            user_id = data[0]
            old = data[1]
        else:
            user_id = int(target)
            old, _ = get_user(user_id, "")
        new = old + amount
        set_user(user_id, new)
        bot.send_message(user_id, f"✅ {amount} Credits Added\n💰 New Balance: {new} Credits")
        bot.reply_to(m, f"✅ Added {amount} Credits\nUser: {user_id}\nTotal: {new}")
    except Exception as e:
        bot.reply_to(m, f"Error: {str(e)}\nUsage: /add @username amount")

@bot.message_handler(commands=['stats'])
def stats(m):
    if m.chat.type != "private":
        return
    if not is_admin(m.from_user.id):
        return
    total = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_credits = cursor.execute("SELECT SUM(credits) FROM users").fetchone()[0] or 0
    verified_count = cursor.execute("SELECT COUNT(*) FROM users WHERE verified=1").fetchone()[0]
    
    stats_msg = f"""
╔════════════════════════════════════════╗
║     📊 <b>BOT STATISTICS</b> 📊           ║
╚════════════════════════════════════════╝

<b>👥 Total Users:</b> {total}
<b>✅ Verified Users:</b> {verified_count}
<b>💰 Total Credits:</b> {total_credits}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ <b>Bot running smoothly</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👨‍💻 <b>@Gautamxlive</b>
"""
    bot.send_message(m.chat.id, stats_msg, parse_mode="HTML")

# ============ TEXT BUTTONS HANDLER (ONLY FOR PRIVATE) ============
@bot.message_handler(func=lambda m: True)
def text_buttons(m):
    # Group mein text buttons kaam nahi karenge
    if m.chat.type != "private":
        return
    
    if not check_verification(m.from_user.id):
        start(m)
        return

    text = m.text.lower()
    
    if text == "📱 num info":
        can_proceed, bal = check_credits(m.from_user.id, "private")
        if not can_proceed:
            bot.reply_to(m, "❌ <b>Insufficient Credits!</b>\n\nUse Buy Credits button to recharge.", parse_mode="HTML")
            return
        bot.send_message(m.chat.id, f"""
<b>📱 NUM INFO</b>
─────────────────────────────────────────
💰 Balance: {bal} Credits
⚡ Charge: 1 credit

🔍 Enter Indian phone number
Example: 6205923286
""", parse_mode="HTML")
        bot.register_next_step_handler(m, lambda x: process(x, "phone", x.text, "private"))
        
    elif text == "👤 num to name":
        can_proceed, bal = check_credits(m.from_user.id, "private")
        if not can_proceed:
            bot.reply_to(m, "❌ <b>Insufficient Credits!</b>\n\nUse Buy Credits button to recharge.", parse_mode="HTML")
            return
        bot.send_message(m.chat.id, f"""
<b>👤 NUM TO NAME</b>
─────────────────────────────────────────
💰 Balance: {bal} Credits
⚡ Charge: 1 credit

🔍 Enter Indian phone number
Example: 6205923286
""", parse_mode="HTML")
        bot.register_next_step_handler(m, lambda x: process(x, "name", x.text, "private"))
        
    elif text == "👨‍👩‍👦 family info":
        can_proceed, bal = check_credits(m.from_user.id, "private")
        if not can_proceed:
            bot.reply_to(m, "❌ <b>Insufficient Credits!</b>\n\nUse Buy Credits button to recharge.", parse_mode="HTML")
            return
        bot.send_message(m.chat.id, f"""
<b>👨‍👩‍👦 FAMILY INFO</b>
─────────────────────────────────────────
💰 Balance: {bal} Credits
⚡ Charge: 1 credit

🔍 Enter Aadhar number
Example: 400204118594
""", parse_mode="HTML")
        bot.register_next_step_handler(m, lambda x: process(x, "aadhar", x.text, "private"))
        
    elif text == "💎 tg to num":
        can_proceed, bal = check_credits(m.from_user.id, "private")
        if not can_proceed:
            bot.reply_to(m, "❌ <b>Insufficient Credits!</b>\n\nUse Buy Credits button to recharge.", parse_mode="HTML")
            return
        bot.send_message(m.chat.id, f"""
<b>💎 TG TO NUM</b>
─────────────────────────────────────────
💰 Balance: {bal} Credits
⚡ Charge: 1 credit

🔍 Enter Telegram username
Example: @syko_killer
""", parse_mode="HTML")
        bot.register_next_step_handler(m, lambda x: process(x, "tguser", x.text, "private"))
        
    elif text == "🔄 tg user to number":
        can_proceed, bal = check_credits(m.from_user.id, "private")
        if not can_proceed:
            bot.reply_to(m, "❌ <b>Insufficient Credits!</b>\n\nUse Buy Credits button to recharge.", parse_mode="HTML")
            return
        bot.send_message(m.chat.id, f"""
<b>🔄 TG USER TO NUMBER</b>
─────────────────────────────────────────
💰 Balance: {bal} Credits
⚡ Charge: 1 credit

🔍 Enter Telegram User ID
Example: 123456789
""", parse_mode="HTML")
        bot.register_next_step_handler(m, lambda x: process(x, "tg", x.text, "private"))
        
    elif text == "🚘 vehicle info":
        can_proceed, bal = check_credits(m.from_user.id, "private")
        if not can_proceed:
            bot.reply_to(m, "❌ <b>Insufficient Credits!</b>\n\nUse Buy Credits button to recharge.", parse_mode="HTML")
            return
        bot.send_message(m.chat.id, f"""
<b>🚘 VEHICLE INFO</b>
─────────────────────────────────────────
💰 Balance: {bal} Credits
⚡ Charge: 1 credit

🔍 Enter Vehicle Number
Example: MP16CB6745
""", parse_mode="HTML")
        bot.register_next_step_handler(m, lambda x: process(x, "vehicle", x.text.upper(), "private"))
        
    elif text == "💰 buy credits":
        bot.send_message(m.chat.id, stylish_recharge_message(), reply_markup=stylish_recharge_keyboard(), parse_mode="HTML")
        
    elif text == "👤 my account":
        bal, _ = get_user(m.from_user.id, m.from_user.username)
        account_msg = f"""
╔════════════════════════════════════════╗
║     👤 <b>MY ACCOUNT</b> 👤               ║
╚════════════════════════════════════════╝

<b>🆔 User ID:</b> <code>{m.from_user.id}</code>
<b>👤 Username:</b> @{m.from_user.username or 'None'}
<b>💰 Credits:</b> <b>{bal}</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 <b>Need more credits?</b>
Click on <b>Buy Credits</b> button
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👨‍💻 <b>@Gautamxlive</b>
"""
        bot.send_message(m.chat.id, account_msg, parse_mode="HTML")

def process(m, t, query_value, chat_type):
    uid = m.from_user.id
    username = m.from_user.username
    
    # Only deduct credit in private chat
    if chat_type == "private" and not is_admin(uid):
        bal, _ = get_user(uid, username)
        if bal <= 0:
            bot.reply_to(m, "❌ <b>Insufficient Credits!</b>\n\nUse /buy or click Buy Credits button to recharge.", parse_mode="HTML")
            return

    load = loading(m.chat.id)
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        if t == "phone":
            url = f"https://anon-num-info.vercel.app/num?key=Arpitxlive274&num={query_value}"
        elif t == "name":
            url = f"https://anon-num-info.vercel.app/name?key=Arpitxlive284&num={query_value}"
        elif t == "aadhar":
            url = f"https://anon-family-info.vercel.app/aadhar?key=Arpitxlive284&q={query_value}"
        elif t == "vehicle":
            url = f"https://chola2x-rc2.vercel.app/vehicle?number={query_value}"
        elif t == "tguser":
            url = f"https://anon-tg-info.vercel.app/tg2num/user?key=Arpitxlive205&q={query_value}"
        else:
            url = f"https://anon-tg-info.vercel.app/tg2num/userid?key=Arpitxlive294&q={query_value}"

        r = requests.get(url, headers=headers, timeout=15)
        try:
            data = r.json()
        except:
            data = {"result": r.text}

        bot.delete_message(m.chat.id, load.message_id)
        json_result = format_json_only(data, t, query_value)
        numbers = extract_numbers_from_json(data)
        
        if numbers:
            copy_kb = InlineKeyboardMarkup(row_width=2)
            for num in numbers:
                copy_kb.add(InlineKeyboardButton(f"📱 Copy: {num}", callback_data=f"copy_{num}"))
            bot.send_message(m.chat.id, json_result, reply_markup=copy_kb, parse_mode="HTML")
        else:
            bot.send_message(m.chat.id, json_result, parse_mode="HTML")

        # Deduct credit only in private chat and send notification
        if chat_type == "private" and not is_admin(uid):
            bal, _ = get_user(uid, username)
            new_bal = bal - 1
            set_user(uid, new_bal)
            
            # Get service name
            service_names = {
                "phone": "Num Info",
                "name": "Num To Name",
                "aadhar": "Family Info",
                "vehicle": "Vehicle Info",
                "tguser": "TG To Num",
                "tg": "TG User To Num"
            }
            service_name = service_names.get(t, "Unknown")
            
            # Send usage notification to admin
            send_credit_usage_notification(uid, username, service_name, new_bal)
            
            # Check low credit
            send_low_credit_notification(uid, username, new_bal)
            
            # Send remaining balance to user
            if new_bal <= 3:
                balance_msg = f"""
⚠️ <b>Low Credit Alert!</b>

💰 <b>Remaining Balance:</b> {new_bal} Credits
💡 <b>Please recharge soon!</b>

Use <b>Buy Credits</b> button to recharge.
"""
                bot.send_message(m.chat.id, balance_msg, parse_mode="HTML")
            else:
                bot.send_message(m.chat.id, f"💎 <b>Remaining Balance: {new_bal} Credits</b>", parse_mode="HTML")
            
    except Exception as e:
        bot.edit_message_text(f"❌ <b>Error!</b>\n\n<code>{str(e)[:200]}</code>", m.chat.id, load.message_id, parse_mode="HTML")

if __name__ == "__main__":
    print("=" * 50)
    print("🤖 GAUTAM X INFO BOT")
    print("=" * 50)
    try:
        bot_info = bot.get_me()
        print(f"✅ Bot: @{bot_info.username}")
    except:
        print("❌ Invalid Bot Token! Please check BOT_TOKEN")
        exit(1)
    print(f"👨‍💻 Developer: @Gautamxlive")
    print("=" * 50)
    print("🟢 Bot is running...")
    print("📍 PRIVATE: 15 FREE Credits + Keyboard Buttons")
    print("📍 GROUP: UNLIMITED FREE (Commands Only)")
    print("📍 Admin will receive stylish notifications")
    print("=" * 50)
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        bot.infinity_polling(timeout=60, interval=1)
    except KeyboardInterrupt:
        print("\n🔴 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")