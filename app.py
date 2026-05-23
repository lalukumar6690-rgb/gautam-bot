import telebot
from telebot.types import *
import requests
import sqlite3
import json
import re

BOT_TOKEN = "8717813336:AAHhZP_AFg4icVwdA1n2wCQd0YpVlpSLVvs"

CHANNELS = ["@aghunter", "@nibhadarling", "@infobotfreet"]
ADMIN_ID = 8643031554
UPI_ID = "9939738510@fam"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

conn = sqlite3.connect("db.sqlite", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    credits INTEGER DEFAULT 15,
    verified INTEGER DEFAULT 0
)
''')
conn.commit()

def is_admin(uid):
    return uid == ADMIN_ID

def get_user(uid, username=""):
    cursor.execute("SELECT credits, verified FROM users WHERE user_id=?", (uid,))
    data = cursor.fetchone()
    if not data:
        verified = 1 if is_admin(uid) else 0
        cursor.execute("INSERT INTO users VALUES (?,?,?,?)", (uid, username, 15, verified))
        conn.commit()
        return 15, bool(verified)
    cursor.execute("UPDATE users SET username=? WHERE user_id=?", (username, uid))
    conn.commit()
    return data[0], bool(data[1])

def set_user(uid, credits):
    cursor.execute("UPDATE users SET credits=? WHERE user_id=?", (credits, uid))
    conn.commit()

def set_verified(uid, status):
    cursor.execute("UPDATE users SET verified=? WHERE user_id=?", (1 if status else 0, uid))
    conn.commit()

def check_verified(uid):
    if is_admin(uid):
        return True
    _, verified = get_user(uid, "")
    return verified

def join_kb():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🔗 CHANNEL 1", url="https://t.me/aghunter"))
    kb.add(InlineKeyboardButton("🔗 CHANNEL 2", url="https://t.me/nibhadarling"))
    kb.add(InlineKeyboardButton("🔗 CHANNEL 3", url="https://t.me/infobotfreet"))
    kb.add(InlineKeyboardButton("✅ VERIFY", callback_data="verify"))
    return kb

@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify_callback(call):
    uid = call.from_user.id
    if check_verified(uid):
        bot.answer_callback_query(call.id, "Already verified!")
        return
    all_joined = True
    for ch in CHANNELS:
        try:
            member = bot.get_chat_member(ch, uid)
            if str(member.status).lower() not in ["member", "administrator", "creator"]:
                all_joined = False
                break
        except:
            all_joined = False
            break
    if all_joined:
        set_verified(uid, True)
        bot.answer_callback_query(call.id, "✅ Verified!", show_alert=True)
        bot.edit_message_text("✅ VERIFIED!\n\nSend /start to use bot", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Join all channels first!", show_alert=True)

def private_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("📱 Num Info", "👤 Num To Name")
    kb.add("👨‍👩‍👦 Family Info", "💎 TG To Num")
    kb.add("🔄 TG User To Number", "🚘 Vehicle Info")
    kb.add("💰 Buy Credits", "👤 My Account")
    return kb

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    get_user(uid, m.from_user.username)
    if not check_verified(uid):
        bot.send_message(m.chat.id, "⚠️ VERIFICATION REQUIRED\n\nJoin all channels and click VERIFY:", reply_markup=join_kb())
        return
    if m.chat.type == "private":
        bal, _ = get_user(uid, "")
        bot.send_message(m.chat.id, f"✨ Welcome {m.from_user.first_name}!\n\n💰 Balance: {bal} Credits\n⚡ 1 Credit per search\n\nClick any button below:", reply_markup=private_menu())
    else:
        bot.send_message(m.chat.id, f"🎉 GROUP MODE - FREE\n\nCommands:\n/num 9876543210\n/name 9876543210\n/family 400204118594\n/tg @username\n/tgid 123456789\n/vehicle MP16CB6745")

@bot.message_handler(commands=['num', 'name', 'family', 'tg', 'tgid', 'vehicle'])
def handle_commands(m):
    if not check_verified(m.from_user.id):
        start(m)
        return
    cmd = m.text.split()[0][1:]
    try:
        value = m.text.split()[1]
        if cmd in ["num", "name"] and not re.match(r'^\d{10}$', value):
            bot.reply_to(m, "❌ Invalid phone number")
            return
        process(m, cmd, value, m.chat.type)
    except:
        bot.reply_to(m, f"❌ Usage: /{cmd} [value]")

@bot.message_handler(commands=['buy'])
def buy_cmd(m):
    if m.chat.type != "private":
        return
    msg = f"💰 RECHARGE\n\n10 Credits = ₹50\n20 = ₹90\n50 = ₹200\n100 = ₹350\n\n💳 UPI: {UPI_ID}\n\nAfter payment contact @SYKO_KILLER"
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("👨‍💻 CONTACT ADMIN", url="https://t.me/SYKO_KILLER"))
    bot.send_message(m.chat.id, msg, reply_markup=kb)

@bot.message_handler(func=lambda m: m.chat.type == "private")
def text_handler(m):
    if not check_verified(m.from_user.id):
        start(m)
        return
    text = m.text.lower()
    bal, _ = get_user(m.from_user.id, "")
    if bal <= 0 and "buy" not in text and "my account" not in text:
        bot.reply_to(m, "❌ Insufficient credits! Use /buy")
        return
    if text == "📱 num info":
        bot.send_message(m.chat.id, "Enter 10 digit phone number:")
        bot.register_next_step_handler(m, lambda x: process(x, "phone", x.text, "private"))
    elif text == "👤 num to name":
        bot.send_message(m.chat.id, "Enter 10 digit phone number:")
        bot.register_next_step_handler(m, lambda x: process(x, "name", x.text, "private"))
    elif text == "👨‍👩‍👦 family info":
        bot.send_message(m.chat.id, "Enter Aadhar number:")
        bot.register_next_step_handler(m, lambda x: process(x, "aadhar", x.text, "private"))
    elif text == "💎 tg to num":
        bot.send_message(m.chat.id, "Enter Telegram username (with @):")
        bot.register_next_step_handler(m, lambda x: process(x, "tguser", x.text, "private"))
    elif text == "🔄 tg user to number":
        bot.send_message(m.chat.id, "Enter Telegram User ID:")
        bot.register_next_step_handler(m, lambda x: process(x, "tg", x.text, "private"))
    elif text == "🚘 vehicle info":
        bot.send_message(m.chat.id, "Enter Vehicle Number:")
        bot.register_next_step_handler(m, lambda x: process(x, "vehicle", x.text.upper(), "private"))
    elif text == "💰 buy credits":
        buy_cmd(m)
    elif text == "👤 my account":
        bot.send_message(m.chat.id, f"👤 MY ACCOUNT\n\n🆔 ID: {m.from_user.id}\n💰 Balance: {bal} Credits")

def process(m, t, value, chat_type):
    uid = m.from_user.id
    if chat_type == "private" and not is_admin(uid):
        bal, _ = get_user(uid, "")
        if bal <= 0:
            bot.reply_to(m, "❌ Insufficient credits!")
            return
    msg = bot.send_message(m.chat.id, "⏳ Processing...")
    try:
        urls = {
            "phone": f"https://anon-num-info.vercel.app/num?key=Arpitxlive274&num={value}",
            "name": f"https://anon-num-info.vercel.app/name?key=Arpitxlive284&num={value}",
            "aadhar": f"https://anon-family-info.vercel.app/aadhar?key=Arpitxlive284&q={value}",
            "vehicle": f"https://chola2x-rc2.vercel.app/vehicle?number={value}",
            "tguser": f"https://anon-tg-info.vercel.app/tg2num/user?key=Arpitxlive205&q={value}",
            "tg": f"https://anon-tg-info.vercel.app/tg2num/userid?key=Arpitxlive294&q={value}"
        }
        r = requests.get(urls[t], timeout=15)
        data = r.json() if r.text else {"result": r.text}
        data["developer"] = "@Gautamxlive"
        bot.delete_message(m.chat.id, msg.message_id)
        json_output = json.dumps(data, indent=2, ensure_ascii=False)
        if len(json_output) > 4000:
            json_output = json_output[:4000] + "\n... truncated"
        bot.send_message(m.chat.id, f"<code>{json_output}</code>\n\n👨‍💻 @Gautamxlive")
        if chat_type == "private" and not is_admin(uid):
            bal, _ = get_user(uid, "")
            set_user(uid, bal - 1)
            bot.send_message(m.chat.id, f"💎 Remaining: {bal - 1} Credits")
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)[:100]}", m.chat.id, msg.message_id)

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()