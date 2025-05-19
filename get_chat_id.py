from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio  

TG_TOKEN = "8109434457:AAHA6g55xzsTW4yZELE-2blQ7kHnJlS6ZNo"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"Your chat ID is: {chat_id}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TG_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    asyncio.run(app.run_polling())
