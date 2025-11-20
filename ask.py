import requests
import telebot
from telebot import types
import discord
import threading


# ====== CONFIG ======
TELEGRAM_TOKEN = "7698723495:AAFxkZJZujFcci0fn6fEGTOvtwB4Eyw0G3c"

# 👉 Ở ĐÂY — Bạn thay token Discord mới vào đây (KHÔNG gửi lên đây)
DISCORD_TOKEN = "MTQ0MDI5NjM2NzkwMDU5MDIyMQ.G0g_gF.cwUwZoNnV6Sve5ThQaDuNYrpSZk0R7DvOSOFVE"

API_BASE = "https://bj-microsoft-search-ai.vercel.app/"


# ====== API SEARCH ======
def call_search_api(query: str):
    try:
        resp = requests.get(API_BASE, params={"chat": query}, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        if "ok" not in data:
            data["ok"] = True
        return data
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =============================================================
# ======================== TELEGRAM BOT ========================
# =============================================================

bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="Markdown")

bot.remove_webhook()   # tránh lỗi 409


@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 Xin chào!\n"
        "Dùng `/ask <câu hỏi>` để hỏi bot.\n"
    )


@bot.message_handler(commands=["ask"])
def handle_ask(message):
    parts = message.text.split(" ", 1)
    query = parts[1].strip() if len(parts) > 1 else "ngày thành lập discord"

    waiting = bot.reply_to(message, f"🔎 Đang tra cứu: _{query}_ ...")

    result = call_search_api(query)

    if not result.get("ok"):
        bot.edit_message_text(
            f"❌ Lỗi API:\n`{result.get('error')}`",
            chat_id=waiting.chat.id,
            message_id=waiting.message_id,
        )
        return

    text = result.get("text", "Không có dữ liệu.")
    bot.edit_message_text(text, waiting.chat.id, waiting.message_id)

    citations = result.get("citations", [])
    if citations:
        kb = types.InlineKeyboardMarkup()
        for c in citations[:6]:
            title = (c.get("title") or "Nguồn")[:40]
            url = c.get("url")
            if url:
                kb.add(types.InlineKeyboardButton(title, url=url))
        bot.send_message(waiting.chat.id, "🔗 Nguồn tham khảo:", reply_markup=kb)


def run_telegram():
    print("🤖 Telegram Bot đang chạy…")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)


# =============================================================
# ======================== DISCORD BOT =========================
# =============================================================

intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)


@discord_client.event
async def on_ready():
    print(f"🟦 Discord Bot đã đăng nhập: {discord_client.user}")


@discord_client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith("!ask"):
        query = message.content.replace("!ask", "").strip()
        if query == "":
            query = "ngày thành lập discord"

        await message.channel.send(f"🔍 Đang tra cứu **{query}** ...")

        result = call_search_api(query)

        if not result.get("ok"):
            await message.channel.send(f"❌ Lỗi API:\n`{result['error']}`")
            return

        await message.channel.send(result.get("text", "Không có nội dung."))


def run_discord():
    discord_client.run(DISCORD_TOKEN)


# =============================================================
# ====================== CHẠY 2 BOT CÙNG LÚC ==================
# =============================================================

if __name__ == "__main__":
    t1 = threading.Thread(target=run_telegram)
    t2 = threading.Thread(target=run_discord)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
