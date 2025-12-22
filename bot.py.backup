# app/bot.py
# 알람주기, 안내, 각종 커맨드, RSS스케줄링, 일반 텍스트 검색 등
# main 실행 함수

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
from app.news import search_news, get_news_with_images
from app.storage import get_keywords, add_keyword, remove_keyword
from app.rss.rss_fetcher import fetch_new_articles
from app.super_controller import super_controller

# ------------------ 뉴스 스코어링 및 클러스터링 관련 ----------------
from app.scoring.keyword_scoring import score_and_filter_articles_for_chat
from app.clustering.news_clusterer import cluster_scored_articles

# chat_id -> asyncio.Task 매핑
rss_tasks: dict[int, asyncio.Task] = {}


# ---------------- 기본 안내 ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = super_controller.get_start_message()
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
    """
    등록된 모든 관심 키워드에 대해 뉴스를 검색
    """
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

    # 각 키워드별로 검색
    for kw in keywords:
        # 검색용 쿼리: 맨 앞의 '-'는 떼고 사용
        query_kw = kw.lstrip("-").strip()
        if not query_kw:
            continue

        await update.message.reply_text(f"🔎 [{kw}] 관련 뉴스")
        
        # 이미지와 함께 뉴스 가져오기
        news_items = get_news_with_images(query_kw, chat_id=chat_id)
        
        # 각 뉴스를 개별 메시지로 전송
        await send_news_with_images(update, news_items)


# ---------------- RSS 수동 조회 ----------------

async def rss_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """RSS에서 새 기사를 확인하고 표시"""
    chat_id = update.effective_chat.id

    await update.message.reply_text("RSS에서 새 기사를 확인 중입니다...")

    articles = fetch_new_articles()

    if not articles:
        await update.message.reply_text("새로운 RSS 기사가 없습니다.")
        return

    # 스코어링
    scored = score_and_filter_articles_for_chat(articles, chat_id)
    if not scored:
        await update.message.reply_text("필터/스코어 기준에 맞는 RSS 기사가 없습니다.")
        return

    # 클러스터링 (중복 제거)
    clustered = cluster_scored_articles(scored)
    
    await update.message.reply_text("📰 새로 들어온 RSS 기사:")
    
    # 이미지와 함께 전송
    news_items = []
    for cluster in clustered:
        main = cluster.main_article
        a = main.article
        news_items.append({
            'title': a.get("title", "제목 없음"),
            'url': a.get("link", a.get("url", "")),
            'image_url': a.get("urlToImage", ""),
            'source': "",
            'score': main.score
        })
    
    await send_news_with_images(update, news_items)


# ---------------- 뉴스 이미지 전송 헬퍼 ----------------

async def send_news_with_images(update: Update, news_items: list):
    """
    뉴스 목록을 이미지와 함께 개별 메시지로 전송
    
    Args:
        update: Telegram Update 객체
        news_items: [{'title', 'url', 'image_url', 'source', 'score'}, ...]
    """
    if not news_items:
        await update.message.reply_text("표시할 뉴스가 없습니다.")
        return
    
    for item in news_items:
        title = item['title']
        url = item['url']
        image_url = item.get('image_url', '')
        source = item.get('source', '')
        score = item.get('score', 0)
        
        # 캡션 생성
        caption = f"[{score:+}] {title}"
        if source:
            caption += f"\n📡 {source}"
        caption += f"\n🔗 {url}"
        
        # 이미지가 있으면 photo로, 없으면 텍스트로
        try:
            if image_url and image_url.startswith('http'):
                await update.message.reply_photo(
                    photo=image_url,
                    caption=caption
                )
            else:
                # 이미지 없으면 텍스트만
                await update.message.reply_text(
                    f"• {caption}"
                )
        except Exception as e:
            # 이미지 로드 실패 시 텍스트로 폴백
            await update.message.reply_text(
                f"• {caption}"
            )
        
        # 메시지 간 간격 (텔레그램 rate limit 방지)
        await asyncio.sleep(0.3)


# ---------------- RSS 자동 스케줄링 (asyncio 기반) ----------------

async def rss_auto_loop(chat_id: int, bot):
    """
    특정 chat_id에 대해 주기적으로 RSS를 확인하고 결과를 보내는 루프.
    """
    try:
        # 처음 바로 메시지 안 나가게, 한 번 기다렸다가 시작
        interval = super_controller.get_rss_auto_interval()
        await asyncio.sleep(interval)

        while True:
            articles = fetch_new_articles()
            now_str = datetime.now().strftime("%H:%M:%S")

            interval = super_controller.get_rss_auto_interval()

            if articles:
                scored = score_and_filter_articles_for_chat(articles, chat_id)
                if scored:
                    # 클러스터링 (중복 제거)
                    clustered = cluster_scored_articles(scored)
                    
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"🛰 새로 들어온 RSS 기사 ({now_str}):"
                    )
                    
                    # 이미지와 함께 전송 (상위 3개만)
                    news_items = []
                    for cluster in clustered[:3]:
                        main = cluster.main_article
                        a = main.article
                        news_items.append({
                            'title': a.get("title", "제목 없음"),
                            'url': a.get("link", a.get("url", "")),
                            'image_url': a.get("urlToImage", ""),
                            'source': "",
                            'score': main.score
                        })
                    
                    for item in news_items:
                        title = item['title']
                        url = item['url']
                        image_url = item.get('image_url', '')
                        score = item.get('score', 0)
                        
                        caption = f"[{score:+}] {title}\n🔗 {url}"
                        
                        try:
                            if image_url and image_url.startswith('http'):
                                await bot.send_photo(
                                    chat_id=chat_id,
                                    photo=image_url,
                                    caption=caption
                                )
                            else:
                                await bot.send_message(
                                    chat_id=chat_id,
                                    text=f"• {caption}"
                                )
                        except Exception:
                            await bot.send_message(
                                chat_id=chat_id,
                                text=f"• {caption}"
                            )
                        
                        await asyncio.sleep(0.3)
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"🔁 {now_str} 기준 새 RSS 기사 없음 (주기 {interval}초 체크 중)",
                )

            await asyncio.sleep(interval)
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

    interval = super_controller.get_rss_auto_interval()
    await update.message.reply_text(
        f"⏱ RSS 자동 알림을 {interval}초 간격으로 시작합니다."
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
    """
    일반 텍스트 입력 시 뉴스 검색
    """
    chat_id = update.effective_chat.id
    query = (update.message.text or "").strip()
    if not query:
        await update.message.reply_text("검색어를 입력해주세요.")
        return

    await update.message.reply_text(f"🔎 검색어: {query}\n뉴스를 찾는 중입니다...")
    
    # 이미지와 함께 뉴스 가져오기
    news_items = get_news_with_images(query, chat_id=chat_id)
    
    # 각 뉴스를 개별 메시지로 전송
    await send_news_with_images(update, news_items)


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
