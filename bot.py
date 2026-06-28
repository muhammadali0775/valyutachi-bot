import requests
import json
import os
import asyncio
from datetime import datetime
from telegram import Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
import pytz

from groq import Groq
GROQ_KEY = "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"
groq_client = Groq(api_key=GROQ_KEY)
BOT_TOKEN = "8869250752:AAEsqGxLO-3yOkw00XqWJSabChso-XHFFzE"
ADMIN_ID = 6165734345
REKLAMA = {
    "matn": "",
    "boshlanish": "",
    "tugash": "",
}
SUBS_FILE = "subscribers.json"
TASHKENT = pytz.timezone("Asia/Tashkent")

def load_subscribers():
    if not os.path.exists(SUBS_FILE):
        return []
    with open(SUBS_FILE, "r") as f:
        return json.load(f)

def save_subscribers(lst):
    with open(SUBS_FILE, "w") as f:
        json.dump(lst, f, indent=2)

def add_subscriber(chat_id):
    lst = load_subscribers()
    if chat_id not in lst:
        lst.append(chat_id)
        save_subscribers(lst)

def remove_subscriber(chat_id):
    lst = [i for i in load_subscribers() if i != chat_id]
    save_subscribers(lst)

def get_dollar_rate():
    try:
        res = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/USD/")
        data = res.json()[0]
        return float(data["Rate"]), data["Date"]
    except Exception as e:
        print(f"Xato: {e}")
        return None, None

def build_message():
    rate, date = get_dollar_rate()
    if not rate:
        return "Kurs olinmadi."
    now = datetime.now(TASHKENT).strftime("%H:%M, %d.%m.%Y")
    return (f"💵 *Dollar kursi — {date}*\n\n"
            f"1 USD = *{rate:,.0f} UZS*\n\n"
            f"100 USD = *{rate*100:,.0f} UZS*\n\n"    
            f"🏦 Markaziy Bank\n🕐 {now}")

async def send_to_all(bot):
    from datetime import datetime
    msg = build_message()
    hozir = datetime.now(TASHKENT).strftime("%d.%m.%Y %H:%M")
    for chat_id in load_subscribers():
        try:
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
            if REKLAMA["matn"] and REKLAMA["boshlanish"] <= hozir <= REKLAMA["tugash"]:
                await bot.send_message(chat_id=chat_id, text=f"📣 *Reklama*\n\n{REKLAMA['matn']}", parse_mode="Markdown")
        except Exception as e:
            print(f"Xato: {e}")

async def start(update, context):
    add_subscriber(update.effective_chat.id)
    await update.message.reply_text("👋 Salom! Har kuni 09:00 da kurs yuboraman.\n/kurs /stop")

async def kurs(update, context):
    await update.message.reply_text(build_message(), parse_mode="Markdown")

async def stop(update, context):
    remove_subscriber(update.effective_chat.id)
    await update.message.reply_text("Obunadan chiqdingiz. /start bilan qayta qo'shiling.")

async def ai(update, context):
    savol = " ".join(context.args)
    if not savol:
        await update.message.reply_text("Misol: /ai dollar kursi haqida nima deysiz?")
        return
    await update.message.reply_text("🤔 O'ylamoqda...")
    try:
        javob = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": savol}]
        )
        await update.message.reply_text(javob.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text("Xatolik yuz berdi.")
        
async def reklama(update, context):
    if update.effective_chat.id != ADMIN_ID:
        await update.message.reply_text("❌ Ruxsat yo'q.")
        return
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Misol: /reklama 27.06.2026-09:00 29.06.2026-21:00 Reklama matni")
        return
    REKLAMA["boshlanish"] = args[0]
    REKLAMA["tugash"] = args[1]
    REKLAMA["matn"] = " ".join(args[2:])
    await update.message.reply_text(f"✅ Reklama qo'shildi!\n{args[0]} dan {args[1]} gacha chiqadi.")

async def stats(update, context):
    if update.effective_chat.id != ADMIN_ID:
        await update.message.reply_text("❌ Ruxsat yo'q.")
        return
    count = len(load_subscribers())
    await update.message.reply_text(f"👥 Obunachilar soni: *{count}* ta", parse_mode="Markdown")
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("kurs", kurs))
    app.add_handler(CommandHandler("stop", stop))
    
    app.add_handler(CommandHandler("reklama", reklama))
    app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("ai", ai))
    async def daily_sender(bot):
        from datetime import timedelta
        while True:
            now = datetime.now(TASHKENT)
            target = now.replace(hour=9, minute=0, second=0, microsecond=0)
            if now >= target:
                target += timedelta(days=1)
            await asyncio.sleep((target - now).total_seconds())
            await send_to_all(bot)

    async def run():
        async with app:
            await app.start()
            await app.updater.start_polling()
            await daily_sender(app.bot)

    print("🤖 Bot ishga tushdi...")
    asyncio.run(run())

if __name__ == "__main__":
    main()
