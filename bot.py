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

# Issue #16: 언론사 필터링
from app.database.db_manager import get_db
from app.utils.news_source_mapper import extract_source_from_url, get_all_sources

# ------------------ 뉴스 스코어링 및 클러스터링 관련 ----------------
from app.scoring.keyword_scoring import score_and_filter_articles_for_chat
from app.clustering.news_clusterer import cluster_scored_articles

# chat_id -> asyncio.Task 매핑
rss_tasks: dict[int, asyncio.Task] = {}


# ---------------- 기본 안내 ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """간단한 환영 메시지"""
    await update.message.reply_text(
        "안녕하세요! Leafletter News Bot입니다.\n"
        "뉴스 검색과 맞춤형 알림을 제공합니다.\n\n"
        "사용법을 보려면 /help 명령어를 입력하세요."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """전체 기능 안내"""
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

def filter_by_source(news_items: list, chat_id: int) -> list:
    """
    Issue #16: 사용자의 차단된 언론사에 따라 기사 필터링

    Args:
        news_items: 기사 목록
        chat_id: 사용자 ID

    Returns:
        필터링된 기사 목록
    """
    db = get_db()
    blocked_sources = db.get_blocked_sources(chat_id)

    if not blocked_sources:
        return news_items

    filtered = []
    for item in news_items:
        url = item.get('url') or item.get('link', '')
        source = extract_source_from_url(url)

        # 차단된 언론사가 아니면 포함
        if source not in blocked_sources:
            filtered.append(item)

    return filtered


async def send_news_with_images(update: Update, news_items: list):
    """
    뉴스 목록을 이미지와 함께 개별 메시지로 전송
    ✅ 이슈 #21-4: 썸네일 활성화 및 포맷 통일
    ✅ 이슈 #25: 불필요한 메시지 제거
    ✅ 이슈 #16: 언론사 필터링 적용
    """
    if not news_items:
        return

    # Issue #16: 언론사 필터링
    chat_id = update.effective_chat.id
    news_items = filter_by_source(news_items, chat_id)

    if not news_items:
        return
    
    for item in news_items:
        title = item['title']
        url = item['url']
        image_url = item.get('image_url', '')
        score = item.get('score', 0)
        
        # ✅ 간결한 포맷 (이모티콘 제거)
        caption = f"[{score:+}] {title}\n{url}"
        
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
                    
                    # ✅ 이슈 #25: 헤더 메시지 제거
                    # 바로 기사 전송 시작
                    
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
                    
                    # Issue #16: 언론사 필터링 적용
                    news_items = filter_by_source(news_items, chat_id)

                    # ✅ 이슈 #25: 전송할 기사가 없으면 조용히 넘어감
                    if not news_items:
                        await asyncio.sleep(interval)
                        continue

                    for item in news_items:
                        title = item['title']
                        url = item['url']
                        image_url = item.get('image_url', '')
                        score = item.get('score', 0)
                        
                        # ✅ 간결한 포맷 (이모티콘 제거)
                        caption = f"[{score:+}] {title}\n{url}"
                        
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


# ---------------- 언론사 필터링 (Issue #16) ----------------

async def block_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """언론사 차단"""
    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        await update.message.reply_text(
            "사용법: /block <언론사명>\n"
            "예: /block 조선일보\n"
            "또는: /block chosun.com\n\n"
            "매핑된 언론사 목록을 보려면 /sources 명령어를 사용하세요."
        )
        return

    source = " ".join(args).strip()
    db = get_db()

    # 차단 추가
    if db.block_source(chat_id, source):
        blocked = db.get_blocked_sources(chat_id)
        await update.message.reply_text(
            f"🚫 '{source}' 차단 완료\n\n"
            f"차단된 언론사 ({len(blocked)}):\n" +
            "\n".join(f"• {s}" for s in blocked)
        )
    else:
        await update.message.reply_text(
            f"'{source}'는 이미 차단된 언론사입니다."
        )


async def allow_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """언론사 차단 해제"""
    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        await update.message.reply_text(
            "사용법: /allow <언론사명>\n"
            "예: /allow 조선일보"
        )
        return

    source = " ".join(args).strip()
    db = get_db()

    # 차단 해제
    if db.unblock_source(chat_id, source):
        blocked = db.get_blocked_sources(chat_id)
        if blocked:
            await update.message.reply_text(
                f"✅ '{source}' 차단 해제 완료\n\n"
                f"남은 차단 언론사 ({len(blocked)}):\n" +
                "\n".join(f"• {s}" for s in blocked)
            )
        else:
            await update.message.reply_text(
                f"✅ '{source}' 차단 해제 완료\n\n"
                "이제 차단된 언론사가 없습니다."
            )
    else:
        await update.message.reply_text(
            f"'{source}'는 차단 목록에 없습니다."
        )


async def sources_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """차단된 언론사 목록 표시"""
    chat_id = update.effective_chat.id
    db = get_db()

    blocked = db.get_blocked_sources(chat_id)

    if not blocked:
        msg = "🔓 차단된 언론사가 없습니다.\n\n"
    else:
        msg = f"🚫 차단된 언론사 ({len(blocked)}):\n"
        msg += "\n".join(f"• {s}" for s in blocked)
        msg += "\n\n"

    # 매핑된 주요 언론사 목록 추가
    all_sources = get_all_sources()
    msg += f"📰 매핑된 주요 언론사 ({len(all_sources)}):\n"
    msg += "\n".join(f"• {s}" for s in all_sources[:20])  # 처음 20개만 표시

    if len(all_sources) > 20:
        msg += f"\n... 외 {len(all_sources) - 20}개"

    await update.message.reply_text(msg)


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
    app.add_handler(CommandHandler("help", help_cmd))

    # 관심 키워드 관련
    app.add_handler(CommandHandler("add", add_cmd))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("del", del_cmd))
    app.add_handler(CommandHandler("scan", scan_cmd))

    # RSS 관련
    app.add_handler(CommandHandler("rss_now", rss_now))
    app.add_handler(CommandHandler("rss_auto_on", rss_auto_on))
    app.add_handler(CommandHandler("rss_auto_off", rss_auto_off))

    # 언론사 필터링 (Issue #16)
    app.add_handler(CommandHandler("block", block_cmd))
    app.add_handler(CommandHandler("allow", allow_cmd))
    app.add_handler(CommandHandler("sources", sources_cmd))

    # 일반 텍스트 → 뉴스 검색
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling()


if __name__ == "__main__":
    main()
