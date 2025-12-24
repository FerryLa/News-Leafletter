# bot.py - 이슈 #25 해결 + asyncio 에러 수정
# 알람주기, 안내, 각종 커맨드, RSS스케줄링, 일반 텍스트 검색 등

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

# ⚠️ 수정: fetch_new_articles 대신 fetch_new_articles_async 사용
from app.rss.rss_fetcher import fetch_new_articles_async

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
    ✅ 이슈 #25: 불필요한 중간 메시지 제거
    """
    chat_id = update.effective_chat.id
    keywords = get_keywords(chat_id)

    if not keywords:
        await update.message.reply_text(
            "등록된 관심 키워드가 없습니다.\n먼저 /add 로 키워드를 추가하세요."
        )
        return

    # ✅ 간결한 시작 메시지
    await update.message.reply_text("🔎 뉴스 검색 중...")

    # 각 키워드별로 검색
    for kw in keywords:
        query_kw = kw.lstrip("-").strip()
        if not query_kw:
            continue

        news_items = get_news_with_images(query_kw, chat_id=chat_id)
        
        # ✅ 이슈 #25: 결과가 있을 때만 메시지 전송
        if news_items:
            await update.message.reply_text(f"📰 [{kw}]")
            await send_news_with_images(update, news_items)


# ---------------- RSS 수동 조회 ----------------

async def rss_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    RSS에서 새 기사를 확인하고 표시
    ✅ 이슈 #25: 불필요한 메시지 제거
    ✅ asyncio 에러 수정: fetch_new_articles_async 직접 호출
    """
    chat_id = update.effective_chat.id

    # ✅ 간결한 메시지
    await update.message.reply_text("📡 RSS 확인 중...")

    # ⚠️ 수정: 동기 래퍼 대신 비동기 함수 직접 호출
    result = await fetch_new_articles_async()
    # 반환값이 튜플인지 확인
    if isinstance(result, tuple):
        articles = result[0]
    else:
        articles = result

    if not articles:
        await update.message.reply_text("새로운 기사가 없습니다.")
        return

    # 스코어링
    scored = score_and_filter_articles_for_chat(articles, chat_id)
    if not scored:
        await update.message.reply_text("관심 기사가 없습니다.")
        return

    # 클러스터링
    clustered = cluster_scored_articles(scored)
    
    # ✅ 이슈 #25: 헤더 메시지 제거, 바로 기사 전송
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
    ✅ 이슈 #21-4: 썸네일 활성화 및 포맷 통일
    """
    if not news_items:
        return
    
    for item in news_items:
        title = item['title']
        url = item['url']
        image_url = item.get('image_url', '')
        score = item.get('score', 0)
        
        # ✅ 이슈 #21-4: 간결하고 통일된 포맷
        # 스코어 + 제목 + 링크
        caption = f"[{score:+}] {title}\n🔗 {url}"
        
        # 이미지가 있으면 photo로, 없으면 텍스트로 (썸네일 활성화)
        try:
            if image_url and image_url.startswith('http'):
                # 이미지가 있을 때
                await update.message.reply_photo(
                    photo=image_url,
                    caption=caption
                )
            else:
                # ✅ 이슈 #21-4: 썸네일 활성화
                # 이미지 없어도 웹페이지 미리보기 표시
                await update.message.reply_text(
                    text=caption,
                    disable_web_page_preview=False  # 썸네일 활성화!
                )
        except Exception as e:
            # 에러 발생 시 폴백 (썸네일 없이)
            print(f"메시지 전송 실패: {e}")
            await update.message.reply_text(
                text=caption,
                disable_web_page_preview=True  # 에러 시 썸네일 비활성화
            )
        
        # 메시지 간 간격
        await asyncio.sleep(0.3)


# ---------------- RSS 자동 스케줄링 (asyncio 기반) ----------------

async def rss_auto_loop(chat_id: int, bot):
    """
    특정 chat_id에 대해 주기적으로 RSS를 확인하고 결과를 보내는 루프.
    ✅ 이슈 #25: "새 기사 없음" 메시지 제거
    ✅ asyncio 에러 수정: fetch_new_articles_async 직접 호출
    """
    try:
        interval = super_controller.get_rss_auto_interval()
        await asyncio.sleep(interval)

        while True:
            # ⚠️ 수정: 동기 래퍼 대신 비동기 함수 직접 호출
            result = await fetch_new_articles_async()
            # 반환값이 튜플인지 확인
            if isinstance(result, tuple):
                articles = result[0]
            else:
                articles = result
            
            interval = super_controller.get_rss_auto_interval()

            # ✅ 이슈 #25: 기사가 있을 때만 메시지 전송
            if articles:
                scored = score_and_filter_articles_for_chat(articles, chat_id)
                if scored:
                    clustered = cluster_scored_articles(scored)
                    
                    now_str = datetime.now().strftime("%H:%M:%S")
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"🛰 새 기사 ({now_str})"
                    )
                    
                    # 상위 3개만 전송
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
                        
                        # ✅ 이슈 #21-4: 통일된 포맷
                        caption = f"[{score:+}] {title}\n🔗 {url}"
                        
                        try:
                            if image_url and image_url.startswith('http'):
                                await bot.send_photo(
                                    chat_id=chat_id,
                                    photo=image_url,
                                    caption=caption
                                )
                            else:
                                # ✅ 이슈 #21-4: 썸네일 활성화
                                await bot.send_message(
                                    chat_id=chat_id,
                                    text=caption,
                                    disable_web_page_preview=False  # 썸네일 활성화!
                                )
                        except Exception as e:
                            print(f"RSS 전송 실패: {e}")
                            await bot.send_message(
                                chat_id=chat_id,
                                text=caption,
                                disable_web_page_preview=True  # 에러 시 비활성화
                            )
                        
                        await asyncio.sleep(0.3)
            
            # ✅ 이슈 #25: "새 기사 없음" 메시지 완전 제거
            # 조용히 다음 주기 대기

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
        f"⏱ RSS 자동 알림 시작 ({interval}초 간격)\n"
        "💡 새 기사가 있을 때만 알림이 옵니다."
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
    ✅ 이슈 #25: 불필요한 "검색 중" 메시지 제거
    """
    chat_id = update.effective_chat.id
    query = (update.message.text or "").strip()
    if not query:
        return

    # ✅ 간결한 상태 메시지
    status_msg = await update.message.reply_text("🔎 검색 중...")
    
    news_items = get_news_with_images(query, chat_id=chat_id)
    
    # ✅ 이슈 #25: 상태 메시지 삭제
    try:
        await status_msg.delete()
    except:
        pass
    
    if not news_items:
        await update.message.reply_text("관련 기사를 찾지 못했습니다.")
        return
    
    await send_news_with_images(update, news_items)


# ---------------- main ----------------

def main():
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .job_queue(None)
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

    # 일반 텍스트 → 뉴스 검색
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling()


if __name__ == "__main__":
    main()
