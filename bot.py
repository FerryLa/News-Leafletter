# bot.py
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import TELEGRAM_TOKEN
from news import search_news


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Leafletter News Bot 입니다.\n"
        "검색할 키워드나 종목/이슈를 보내주세요.\n\n"
        "예시)\n"
        "- 삼성전자\n"
        "- 비트코인 뉴스\n"
        "- AI 반도체\n"
        "- FOMC 회의"
    )
    await update.message.reply_text(text)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = (update.message.text or "").strip()
    if not query:
        await update.message.reply_text("검색어를 입력해주세요.")
        return

    await update.message.reply_text(f"🔎 검색어: {query}\n뉴스를 찾는 중입니다...")
    result = search_news(query)
    await update.message.reply_text(result)


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # /start 명령 처리
    app.add_handler(CommandHandler("start", start))
    # 일반 텍스트 메시지 처리
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling()


if __name__ == "__main__":
    main()
