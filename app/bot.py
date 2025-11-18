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
from app.news import search_news
from storage import get_keywords, add_keyword, remove_keyword
from app.rss.rss_fetcher import fetch_new_articles


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "안녕하세요.\n"
        "성장판 독서모임의 Leafletter News Bot 입니다.\n"
        "검색할 키워드나 종목/이슈를 보내면 관련 뉴스를 찾아드립니다.\n\n"
        "기능 안내:\n"
        "- 그냥 텍스트: 해당 키워드로 뉴스 검색\n"
        "- /add 키워드  : 관심 키워드 추가\n"
        "- /list        : 등록한 키워드 목록 보기\n"
        "- /del 키워드  : 관심 키워드 삭제\n"
        "- /scan        : 모든 관심 키워드에 대해 뉴스 한 번에 조회\n\n"
        "예시)\n"
        "/add 비트코인 뉴스\n"
        "/add FOMC 회의\n"
        "/scan\n\n"
        
        "추가 기능 안내:\n"
        "- /rss_now    : RSS에서 새로 들어온 기사 확인\n"
    )
    await update.message.reply_text(text)


# ---- 관심 키워드 관련 명령 ----

async def add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        await update.message.reply_text("사용법: /add 키워드\n예: /add 비트코인 뉴스")
        return

    keyword = " ".join(args).strip()
    keywords = add_keyword(chat_id, keyword)

    await update.message.reply_text(
        f"✅ 관심 키워드 추가: {keyword}\n"
        f"현재 키워드: {', '.join(keywords)}"
    )


async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    keywords = get_keywords(chat_id)

    if not keywords:
        await update.message.reply_text("등록된 관심 키워드가 없습니다.\n/add 로 키워드를 추가해보세요.")
        return

    lines = [f"{idx + 1}. {kw}" for idx, kw in enumerate(keywords)]
    await update.message.reply_text("📌 관심 키워드 목록:\n" + "\n".join(lines))


async def del_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        await update.message.reply_text("사용법: /del 키워드\n예: /del 비트코인 뉴스")
        return

    keyword = " ".join(args).strip()
    before = set(get_keywords(chat_id))
    after = set(remove_keyword(chat_id, keyword))

    if keyword not in before:
        await update.message.reply_text("해당 키워드는 목록에 없습니다.")
        return

    if not after:
        await update.message.reply_text(f"❎ '{keyword}' 삭제 완료.\n이제 등록된 키워드가 없습니다.")
    else:
        await update.message.reply_text(
            f"❎ '{keyword}' 삭제 완료.\n"
            f"남은 키워드: {', '.join(after)}"
        )


async def scan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    keywords = get_keywords(chat_id)

    if not keywords:
        await update.message.reply_text("등록된 관심 키워드가 없습니다.\n먼저 /add 로 키워드를 추가하세요.")
        return

    await update.message.reply_text(
        "📡 관심 키워드에 대한 뉴스를 스캔합니다:\n"
        + "\n".join(f"- {kw}" for kw in keywords)
    )

    # 키워드별로 순차 검색
    for kw in keywords:
        result = search_news(kw)
        header = f"🔎 [{kw}] 관련 뉴스"
        await update.message.reply_text(f"{header}\n\n{result}")


# ---- 일반 텍스트 검색 ----

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = (update.message.text or "").strip()
    if not query:
        await update.message.reply_text("검색어를 입력해주세요.")
        return

    await update.message.reply_text(f"🔎 검색어: {query}\n뉴스를 찾는 중입니다...")
    result = search_news(query)
    await update.message.reply_text(result)

# ---- RSS ----
async def rss_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        articles = fetch_new_articles()
    except Exception as e:
        # 사용자에게는 간단히 안내
        await update.message.reply_text("RSS를 불러오는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
        # 개발용 로그 (나중에 logging 모듈로 바꿔도 좋습니다)
        print(f"[rss_now] fetch_new_articles error: {e}")
        return

    if not articles:
        await update.message.reply_text("새로운 RSS 기사가 없습니다.")
        return


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # 기본 안내
    app.add_handler(CommandHandler("start", start))

    # 관심 키워드 관련
    app.add_handler(CommandHandler("add", add_cmd))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("del", del_cmd))
    app.add_handler(CommandHandler("scan", scan_cmd))

    # 일반 텍스트 → 뉴스 검색
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # RSS 수집기
    app.add_handler(CommandHandler("rss_now", rss_now))

    app.run_polling()





if __name__ == "__main__":
    main()
