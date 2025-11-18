# app/bot.py
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import asyncio
from datetime import datetime
from config import TELEGRAM_TOKEN
from app.news import search_news
from app.storage import get_keywords, add_keyword, remove_keyword
from app.rss.rss_fetcher import fetch_new_articles

# RSS 자동 알림 주기 (초 단위)
AUTO_INTERVAL = 60  # 테스트할 때만 10으로 줄여서 써도 됨

# chat_id -> asyncio.Task 매핑
rss_tasks: dict[int, asyncio.Task] = {}

# ---------------- 기본 안내 ----------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Leafletter News Bot 입니다.\n"
        "검색할 키워드나 종목/이슈를 보내면 관련 뉴스를 찾아드립니다.\n\n"
        "기능 안내:\n"
        "- 텍스트 입력  : 해당 키워드로 뉴스 검색\n"
        "- /add 키워드  : 관심 키워드 추가\n"
        "- /list        : 관심 키워드 목록 보기\n"
        "- /del 키워드  : 관심 키워드 삭제\n"
        "- /scan        : 모든 관심 키워드 뉴스 한 번에 조회\n\n"

        "예시)\n"
        "/add 비트코인 뉴스\n"
        "/add FOMC 회의\n"
        "/scan\n\n"
        
        "추가 기능 안내:\n"
        "- /rss_now     : RSS에서 새로 들어온 기사 수동 확인\n"
        "- /rss_auto_on : RSS 자동 알림 시작\n"
        "- /rss_auto_off: RSS 자동 알림 중지\n\n"

    )
    await update.message.reply_text(text)


# ---------------- 관심 키워드 관리 ----------------


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
        await update.message.reply_text(
            "등록된 관심 키워드가 없습니다.\n/add 로 키워드를 추가해보세요."
        )
        return

    lines = [f"{i + 1}. {kw}" for i, kw in enumerate(keywords)]
    await update.message.reply_text("📌 관심 키워드 목록:\n" + "\n".join(lines))


async def del_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        await update.message.reply_text("사용법: /del 키워드\n예: /del 비트코인 뉴스")
        return

    keyword = " ".join(args).strip()
    before = get_keywords(chat_id)

    if keyword not in before:
        await update.message.reply_text("해당 키워드는 목록에 없습니다.")
        return

    after = remove_keyword(chat_id, keyword)

    if not after:
        await update.message.reply_text(
            f"❎ '{keyword}' 삭제 완료.\n이제 등록된 키워드가 없습니다."
        )
    else:
        await update.message.reply_text(
            f"❎ '{keyword}' 삭제 완료.\n"
            f"남은 키워드: {', '.join(after)}"
        )


async def scan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    keywords = get_keywords(chat_id)

    if not keywords:
        await update.message.reply_text(
            "등록된 관심 키워드가 없습니다.\n먼저 /add 로 키워드를 추가하세요."
        )
        return

    await update.message.reply_text(
        "📡 관심 키워드에 대한 뉴스를 스캔합니다:\n"
        + "\n".join(f"- {kw}" for kw in keywords)
    )

    for kw in keywords:
        result = search_news(kw)
        header = f"🔎 [{kw}] 관련 뉴스"
        await update.message.reply_text(f"{header}\n\n{result}")


# ---------------- RSS 수동 조회 ----------------


async def rss_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("RSS에서 새 기사를 확인 중입니다...")

    articles = fetch_new_articles()

    if not articles:
        await update.message.reply_text("새로운 RSS 기사가 없습니다.")
        return

    lines = []
    for a in articles[:5]:
        title = a.get("title", "제목 없음")
        link = a.get("link", "")
        lines.append(f"• {title}\n{link}")

    await update.message.reply_text("📰 새로 들어온 기사들:\n\n" + "\n\n".join(lines))


# ---------------- RSS 자동 스케줄링 (asyncio 기반) ----------------

import asyncio
rss_tasks: dict[int, asyncio.Task] = {}


async def rss_auto_loop(chat_id: int, bot):
    """
    특정 chat_id에 대해 주기적으로 RSS를 확인하고 결과를 보내는 루프.
    /rss_auto_on 에서 task 생성 직후 바로 메시지가 안 나오게,
    처음 한 번은 AUTO_INTERVAL 만큼 기다렸다가 체크한다.
    """
    try:
        # ✅ 처음 바로 메시지 안 나가게, 한 번 기다렸다가 시작
        await asyncio.sleep(AUTO_INTERVAL)

        while True:
            articles = fetch_new_articles()
            now_str = datetime.now().strftime("%H:%M:%S")

            if articles:
                lines = []
                for a in articles[:3]:
                    title = a.get("title", "제목 없음")
                    link = a.get("link", "")
                    lines.append(f"• {title}\n{link}")

                text = "🛰 새로 들어온 RSS 기사:\n\n" + "\n\n".join(lines)
                await bot.send_message(chat_id=chat_id, text=text)
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"🔁 {now_str} 기준 새 RSS 기사 없음 (주기 {AUTO_INTERVAL}초 체크 중)",
                )

            await asyncio.sleep(AUTO_INTERVAL)
    except asyncio.CancelledError:
        return




async def rss_auto_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    old_task = rss_tasks.get(chat_id)
    if old_task is not None and not old_task.done():
        old_task.cancel()

    task = context.application.create_task(
        rss_auto_loop(chat_id, context.bot)
    )
    rss_tasks[chat_id] = task

    await update.message.reply_text(
        f"⏱ RSS 자동 알림을 {AUTO_INTERVAL}초 간격으로 시작합니다."
    )


async def rss_auto_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    task = rss_tasks.pop(chat_id, None)
    if task is None or task.done():
        await update.message.reply_text("현재 RSS 자동 알림이 켜져 있지 않습니다.")
        return

    task.cancel()
    await update.message.reply_text("⏹ RSS 자동 알림을 중지했습니다.")


# ---------------- 일반 텍스트 검색 ----------------


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = (update.message.text or "").strip()
    if not query:
        await update.message.reply_text("검색어를 입력해주세요.")
        return

    await update.message.reply_text(f"🔎 검색어: {query}\n뉴스를 찾는 중입니다...")
    result = search_news(query)
    await update.message.reply_text(result)


# ---------------- main ----------------


def main():
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .job_queue(None)   # <-- JobQueue 완전히 끔
        .build()
    )

    # 기본 안내
    app.add_handler(CommandHandler("start", start))

    # 관심 키워드 관련
    app.add_handler(CommandHandler("add", add_cmd))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("del", del_cmd))
    app.add_handler(CommandHandler("scan", scan_cmd))

    # RSS 관련
    app.add_handler(CommandHandler("rss_now", rss_now))
    app.add_handler(CommandHandler("rss_auto_on", rss_auto_on))
    app.add_handler(CommandHandler("rss_auto_off", rss_auto_off))

    # 일반 텍스트 → 뉴스 검색 (항상 마지막)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling()


if __name__ == "__main__":
    main()
