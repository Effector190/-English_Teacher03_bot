import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import anthropic

load_dotenv()

TG_TOKEN = os.getenv("TG_BOT_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))

if not TG_TOKEN:
    raise ValueError("TG_BOT_API_KEY not found")

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not found")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

user_modes = {}

SYSTEM_PROMPT = '''
Role:
You are a personal English teacher.

The student level is A1-A2 with a very small vocabulary.

You actively teach:
- correct mistakes
- explain rules simply in Russian
- show natural spoken English

Modes must NOT mix.

MODE 1 - /check

Format:

✅ Исправленная версия:
[correct sentence]

📝 Разбор:
1. mistake -> correction
Правило: simple explanation
В живой речи говорят: natural version

💡 Слово / фраза дня

MODE 2 - /translate

Format:

✅ Твой вариант: user sentence
✔️ Правильно: corrected

📝 Разбор

💡 Слово / фраза дня

If user sends only Russian sentence — ask them to try translating first.

MODE 3 - /chat

Reply with simple A2 English.

---
📝 Разбор
💡 Слово / фраза дня

Rules:

- explanations ONLY in Russian
- English must be simple
- no long introductions
'''


def ask_ai(mode, text):
    prompt = f"Mode: {mode}\nUser message: {text}"
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.content[0].text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "English Teacher Bot\n"
        "/check — проверка текста\n"
        "/translate — проверка перевода\n"
        "/chat — разговор\n"
        "/voice — голос"
    )


async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = update.message.text.replace("/", "")
    user_modes[update.effective_user.id] = mode
    await update.message.reply_text(f"Режим: {mode}")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    mode = user_modes.get(user_id)
    if not mode:
        await update.message.reply_text("Выбери режим: /check /translate /chat /voice")
        return
    answer = ask_ai(mode, text)
    await update.message.reply_text(answer)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Голосовые сообщения пока не поддерживаются в этой версии.")


def main():
    app = ApplicationBuilder().token(TG_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", set_mode))
    app.add_handler(CommandHandler("translate", set_mode))
    app.add_handler(CommandHandler("chat", set_mode))
    app.add_handler(CommandHandler("voice", set_mode))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    print("Bot started...")

    if WEBHOOK_URL:
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TG_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TG_TOKEN}"
        )
    else:
        app.run_polling()


if __name__ == "__main__":
    main()
