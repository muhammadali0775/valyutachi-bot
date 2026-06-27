import requests
import json
import os
import asyncio
from datetime import datetime
from telegram import Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
import pytz

BOT_TOKEN = "8869250752:AAEsqGxLO-3yOkw00XqWJSabChso-XHFFzE"
ADMIN_ID = 6165734345
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
    msg = build_message()
    for chat_id in load_subscribers():
        try:
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
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
    
async def reklama(update, context):
    if update.effective_chat.id != ADMIN_ID:
        await update.message.reply_text("❌ Ruxsat yo'q.")
        return
    matn = " ".join(context.args)
    if not matn:
        await update.message.reply_text("Misol: /reklama Sizning reklamangiz matni")
        return
    subscribers = load_subscribers()
    await update.message.reply_text(f"📤 {len(subscribers)} ta obunachiga yuborilmoqda...")
    for chat_id in subscribers:
        try:
            await context.bot.send_message(chat_id=chat_id, text=f"📢 *Reklama*\n\n{matn}", parse_mode="Markdown")
        except:
            pass
    await update.message.reply_text("✅ Reklama yuborildi!")

async def stats(update, context):
    if update.effective_chat.id != ADMIN_ID:
        await update.message.reply_text("❌ Ruxsat yo'q.")
        return
    count = len(load_subscribers())
    await update.message.reply_text(f"👥 Obunachiler soni: *{count}* ta", parse_mode="Markdown")
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("kurs", kurs))
    app.add_handler(CommandHandler("stop", stop))
    
    app.add_handler(CommandHandler("reklama", reklama))
    app.add_handler(CommandHandler("stats", stats))

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
