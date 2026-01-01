# bot.py - 이슈 #25 해결 + asyncio 에러 수정
# 알람주기, 안내, 각종 커맨드, RSS스케줄링, 일반 텍스트 검색 등

from telegram import Update
import telegram
import telegram.ext
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# MessageReactionHandler 로드 (선택적)
try:
    from telegram.ext import MessageReactionHandler
except (ImportError, AttributeError):
    MessageReactionHandler = None

import asyncio
from datetime import datetime
from config import TELEGRAM_TOKEN
from app.news import search_news, get_news_with_images, get_breaking_news
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
breaking_tasks: dict[int, asyncio.Task] = {}


# ---------------- 기본 안내 ----------------

async def intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """간단한 환영 메시지"""
    await update.message.reply_text(
        "안녕하세요! Leafletter News Bot입니다.\n"
        "뉴스 검색과 맞춤형 알림을 제공합니다.\n\n"
        "사용법을 보려면 /help 명령어를 입력하세요."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """전체 기능 안내"""
    text = (
        "Leafletter News Bot 입니다.\n"
        "검색할 키워드나 종목/이슈를 보내면 관련 뉴스를 찾아드립니다.\n\n"
        "기능 안내:\n"
        "- 텍스트 입력         : 해당 키워드로 뉴스 검색\n"
        "- /add 키워드 [점수]  : 관심 키워드 추가\n"
        "- /list               : 관심 키워드 목록 보기 (점수 포함)\n"
        "- /del 키워드         : 관심 키워드 삭제\n"
        "- /scan               : 모든 관심 키워드 뉴스 한 번에 조회\n"
        "- /scores             : 전체 스코어링 규칙 확인\n\n"
        "키워드 스코어링:\n"
        "- /add 비트코인       -> 비트코인 +1점\n"
        "- /add 기재정정 +3    -> 기재정정 +3점\n"
        "- /add 밈코인 -2      -> 밈코인 -2점\n\n"
        "검색/알림 결과는 점수와 함께 표시됩니다:\n"
        "  • [+3] 비트코인 ETF 승인 임박\n"
        "  • [-2] 밈코인 단기 급등 기사\n\n"
        "고급 기능:\n"
        "- /scoring_help  : 스코어링 고급 기능 안내\n"
        "- /breaking_help : 속보 기능 안내\n"
        "- /themes        : 테마 키워드 목록 확인\n\n"
        "언론사 필터링:\n"
        "- /block 언론사명  : 특정 언론사 기사 차단\n"
        "- /allow 언론사명  : 차단 해제\n"
        "- /sources        : 차단 목록 및 매핑된 언론사 보기\n\n"
        "뉴스 알림:\n"
        "- /start         : 뉴스 자동 알림 시작 (RSS 기반)\n"
        "- /stop          : 뉴스 자동 알림 중지\n"
        "- /rss_now       : RSS에서 새로 들어온 기사 수동 확인\n\n"
        "속보 기능:\n"
        "- /breaking_now  : 실시간 속보 확인\n"
        "- /breaking_auto_on  : 속보 자동 알림 시작 (5분 간격)\n"
        "- /breaking_auto_off : 속보 자동 알림 중지\n\n"
        "피드백:\n"
        "- /like          : 가장 최근 기사에 좋아요\n"
        "- /dislike [이유] : 가장 최근 기사에 싫어요\n"
        "- /feedback      : 내 피드백 통계 보기\n"
        "- 👍/👎 리액션   : 기사 메시지에 이모지 리액션으로 빠른 피드백\n"
    )
    await update.message.reply_text(text)


async def scoring_help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """스코어링 고급 기능 안내"""
    text = (
        "📊 고급 스코어링 기능 안내\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔲 블랙리스트/화이트리스트 스코어링\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "특정 키워드를 포함하거나 제외하는 강력한 필터링\n\n"
        "• /whitelist 키워드\n"
        "  └ 이 키워드를 포함한 뉴스만 표시\n"
        "  └ 예: /whitelist 비트코인\n\n"
        "• /blacklist 키워드\n"
        "  └ 이 키워드를 포함한 뉴스는 무조건 제외\n"
        "  └ 예: /blacklist 광고\n\n"
        "• /remove_whitelist 키워드\n"
        "  └ 화이트리스트에서 제거\n\n"
        "• /remove_blacklist 키워드\n"
        "  └ 블랙리스트에서 제거\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "⏰ 테마 스코어링 (기간 제한)\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "특정 기간 동안만 키워드에 높은 점수 부여\n\n"
        "• /5d_add 키워드   : 5일간 +5점\n"
        "• /20d_add 키워드  : 20일간 +5점\n"
        "• /45d_add 키워드  : 45일간 +5점\n"
        "• /60d_add 키워드  : 60일간 +5점\n"
        "• /120d_add 키워드 : 120일간 +5점\n"
        "• /225d_add 키워드 : 225일간 +5점\n"
        "  └ 예: /20d_add AI규제 (20일간 AI규제 관련 뉴스 +5점)\n"
        "• /themes : 현재 활성화된 테마 키워드 확인\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📂 분류별 스코어링\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "5가지 분류별로 점수를 조정할 수 있습니다\n\n"
        "• /class_add 분류명 점수\n"
        "  └ 분류: 거시경제, 사회정책, 금융, 산업/기술, 문화/생활\n"
        "  └ 예: /class_add 금융 3 (금융 뉴스 +3점)\n"
        "  └ 예: /class_add 문화/생활 -2 (문화/생활 뉴스 -2점)\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎯 최소 스코어 제한\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "• /exclude 최소점수\n"
        "  └ 지정한 점수보다 낮은 뉴스는 표시 안함\n"
        "  └ 예: /exclude 2 (2점 미만 뉴스 제외)\n"
        "  └ 예: /exclude 0 (0점 미만 뉴스 제외)\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📋 스코어링 규칙 확인\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "• /scores\n"
        "  └ 현재 설정된 모든 스코어링 규칙 확인\n"
        "  └ 키워드별 점수, 테마 만료일 등 한눈에 보기\n"
    )
    await update.message.reply_text(text)


async def breaking_help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """속보 기능 안내"""
    text = (
        "📰 속보 기능 안내\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "NewsAPI의 top-headlines를 사용하여\n"
        "한국의 실시간 속보를 가져옵니다.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔔 속보 명령어\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "• /breaking_now\n"
        "  └ 현재 실시간 속보를 즉시 확인합니다\n"
        "  └ 스코어링/필터링이 적용됩니다\n\n"
        "• /breaking_auto_on\n"
        "  └ 속보 자동 알림을 시작합니다 (5분 간격)\n"
        "  └ 새로운 속보만 알림으로 전송됩니다\n"
        "  └ 중복 방지 기능이 적용됩니다\n\n"
        "• /breaking_auto_off\n"
        "  └ 속보 자동 알림을 중지합니다\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 참고사항\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "• 속보에도 키워드 스코어링이 적용됩니다\n"
        "• 언론사 필터링(/block)도 적용됩니다\n"
        "• 이모지 리액션(👍/👎)으로 피드백 가능\n"
        "• /exclude로 설정한 최소 점수도 적용됩니다\n"
    )
    await update.message.reply_text(text)


# ---------------- 관심 키워드 관리 ----------------

async def add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    키워드 추가/업데이트 명령어

    사용법:
    - /add 키워드          -> 키워드에 +1점
    - /add 키워드 +3       -> 키워드에 +3점
    - /add 키워드 -2       -> 키워드에 -2점
    """
    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        await update.message.reply_text(
            "사용법: /add 키워드 [점수]\n\n"
            "예:\n"
            "• /add 비트코인        -> 비트코인 +1점\n"
            "• /add 기재정정 +3     -> 기재정정 +3점\n"
            "• /add 밈코인 -2       -> 밈코인 -2점"
        )
        return

    # 마지막 인자가 숫자인지 확인
    score = 1
    keyword_parts = args

    if len(args) >= 2:
        try:
            # 마지막 인자를 점수로 파싱 시도
            score = int(args[-1])
            keyword_parts = args[:-1]
        except ValueError:
            # 숫자가 아니면 전체를 키워드로 처리
            pass

    keyword = " ".join(keyword_parts).strip()

    if not keyword:
        await update.message.reply_text("키워드를 입력해주세요.")
        return

    # DB에 키워드 추가/업데이트
    from app.database.db_manager import get_db
    db = get_db()
    is_new = db.add_keyword(chat_id, keyword, score)

    # 현재 키워드 목록 가져오기
    keyword_scores = db.get_keywords_with_scores(chat_id)

    action = "추가" if is_new else "업데이트"
    await update.message.reply_text(
        f"✅ '{keyword}' {action}: {score:+}점\n\n"
        f"현재 키워드 ({len(keyword_scores)}):\n" +
        "\n".join(f"  • {k}: {v:+}점" for k, v in keyword_scores.items())
    )


async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """관심 키워드 목록 보기 (점수 포함)"""
    chat_id = update.effective_chat.id

    from app.database.db_manager import get_db
    db = get_db()
    keyword_scores = db.get_keywords_with_scores(chat_id)

    if not keyword_scores:
        await update.message.reply_text(
            "등록된 관심 키워드가 없습니다.\n/add 로 키워드를 추가해보세요."
        )
        return

    lines = []
    for i, (kw, score) in enumerate(keyword_scores.items(), 1):
        lines.append(f"{i}. {kw} ({score:+}점)")

    await update.message.reply_text(
        f"📌 관심 키워드 목록 ({len(keyword_scores)}):\n" + "\n".join(lines)
    )


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
    ✅ 이슈 #36: 최근 기사 저장 (피드백용)
    """
    if not news_items:
        return

    # Issue #16: 언론사 필터링
    chat_id = update.effective_chat.id
    news_items = filter_by_source(news_items, chat_id)

    if not news_items:
        return

    # Issue #36: 첫 번째 기사만 최근 기사로 저장 (피드백용)
    if news_items:
        recent_articles[chat_id] = news_items[0]

    for item in news_items:
        title = item['title']
        url = item['url']
        image_url = item.get('image_url', '')
        score = item.get('score', 0)

        # 간결한 포맷 (점수 + 제목 + 썸네일)
        caption = f"[{score:+}] {title}\n{url}"

        # 이미지가 있으면 photo로, 없으면 텍스트로 (썸네일 활성화)
        sent_message = None
        try:
            if image_url and image_url.startswith('http'):
                # 이미지가 있을 때
                sent_message = await update.message.reply_photo(
                    photo=image_url,
                    caption=caption
                )
            else:
                # 썸네일 활성화
                sent_message = await update.message.reply_text(
                    text=caption,
                    disable_web_page_preview=False  # 썸네일 활성화
                )
        except Exception as e:
            # 에러 발생 시 폴백 (썸네일 없이)
            print(f"메시지 전송 실패: {e}")
            sent_message = await update.message.reply_text(
                text=caption,
                disable_web_page_preview=True  # 에러 시 썸네일 비활성화
            )

        # 메시지 ID를 기사에 매핑 (이모지 리액션 피드백용)
        if sent_message:
            message_to_article[sent_message.message_id] = item

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

                        # 간결한 포맷 (점수 + 제목 + 썸네일)
                        caption = f"[{score:+}] {title}\n{url}"

                        sent_message = None
                        try:
                            if image_url and image_url.startswith('http'):
                                sent_message = await bot.send_photo(
                                    chat_id=chat_id,
                                    photo=image_url,
                                    caption=caption
                                )
                            else:
                                # 썸네일 활성화
                                sent_message = await bot.send_message(
                                    chat_id=chat_id,
                                    text=caption,
                                    disable_web_page_preview=False  # 썸네일 활성화
                                )
                        except Exception as e:
                            print(f"RSS 전송 실패: {e}")
                            sent_message = await bot.send_message(
                                chat_id=chat_id,
                                text=caption,
                                disable_web_page_preview=True  # 에러 시 비활성화
                            )

                        # 메시지 ID를 기사에 매핑 (이모지 리액션 피드백용)
                        if sent_message:
                            message_to_article[sent_message.message_id] = item

                        await asyncio.sleep(0.3)
            
            # ✅ 이슈 #25: "새 기사 없음" 메시지 완전 제거
            # 조용히 다음 주기 대기

            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        return


async def start_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """뉴스 자동 알림 시작 (RSS 기반 + 속보 자동 알림)"""
    chat_id = update.effective_chat.id

    # RSS 자동 알림 시작
    old_rss_task = rss_tasks.get(chat_id)
    if old_rss_task is not None and not old_rss_task.done():
        old_rss_task.cancel()

    rss_task = context.application.create_task(
        rss_auto_loop(chat_id, context.bot)
    )
    rss_tasks[chat_id] = rss_task

    # Issue #36: 속보 자동 알림도 함께 시작
    old_breaking_task = breaking_tasks.get(chat_id)
    if old_breaking_task is not None and not old_breaking_task.done():
        old_breaking_task.cancel()

    breaking_task = context.application.create_task(
        breaking_auto_loop(chat_id, context.bot)
    )
    breaking_tasks[chat_id] = breaking_task

    interval = super_controller.get_rss_auto_interval()
    await update.message.reply_text(
        f"✅ 뉴스 자동 알림 시작!\n"
        f"📰 RSS 뉴스: {interval}초 간격\n"
        f"⚡ 속보 뉴스: 5분 간격\n\n"
        "💡 새 기사가 있을 때만 알림이 옵니다.\n"
        "중지하려면 /stop 을 입력하세요."
    )


async def stop_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """뉴스 자동 알림 중지 (RSS + 속보)"""
    chat_id = update.effective_chat.id

    # RSS 알림 중지
    rss_task = rss_tasks.pop(chat_id, None)
    rss_running = rss_task is not None and not rss_task.done()

    # 속보 알림 중지
    breaking_task = breaking_tasks.pop(chat_id, None)
    breaking_running = breaking_task is not None and not breaking_task.done()

    if not rss_running and not breaking_running:
        await update.message.reply_text(
            "현재 뉴스 자동 알림이 켜져 있지 않습니다.\n"
            "시작하려면 /start 를 입력하세요."
        )
        return

    # 실행 중인 태스크 중지
    if rss_running:
        rss_task.cancel()
    if breaking_running:
        breaking_task.cancel()

    await update.message.reply_text(
        "⏹ 뉴스 자동 알림을 중지했습니다.\n"
        "  - RSS 뉴스 알림 중지\n"
        "  - 속보 뉴스 알림 중지"
    )


# ---------------- 속보 자동 스케줄링 ----------------

async def breaking_auto_loop(chat_id: int, bot):
    """
    속보 자동 알림 루프 (5분 간격)
    """
    from app.database.db_manager import get_db
    import hashlib

    db = get_db()
    interval = 300  # 5분

    try:
        while True:
            try:
                # 속보 가져오기
                breaking_items = get_breaking_news(chat_id)

                # Issue #16: 언론사 필터링 적용
                breaking_items = filter_by_source(breaking_items, chat_id)

                if not breaking_items:
                    await asyncio.sleep(interval)
                    continue

                for item in breaking_items:
                    title = item['title']
                    url = item['url']
                    image_url = item.get('image_url', '')
                    score = item.get('score', 0)

                    # article_id 생성 (중복 체크용)
                    article_id = hashlib.md5(url.encode()).hexdigest()

                    # 이미 전송한 기사인지 확인
                    if db.has_seen_article(article_id):
                        continue

                    # 기사 전송
                    caption = f"[{score:+}] {title}\n{url}"

                    sent_message = None
                    try:
                        if image_url and image_url.startswith('http'):
                            sent_message = await bot.send_photo(
                                chat_id=chat_id,
                                photo=image_url,
                                caption=caption
                            )
                        else:
                            sent_message = await bot.send_message(
                                chat_id=chat_id,
                                text=caption,
                                disable_web_page_preview=False
                            )
                    except Exception as e:
                        print(f"속보 전송 실패: {e}")
                        sent_message = await bot.send_message(
                            chat_id=chat_id,
                            text=caption,
                            disable_web_page_preview=True
                        )

                    # 메시지 ID를 기사에 매핑 (이모지 리액션 피드백용)
                    if sent_message:
                        message_to_article[sent_message.message_id] = item

                    # 캐시에 저장
                    db.mark_article_seen(article_id, url, title)

                    await asyncio.sleep(0.3)

            except Exception as e:
                print(f"속보 자동 알림 오류: {e}")

            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        return


async def breaking_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """실시간 속보 수동 확인"""
    chat_id = update.effective_chat.id

    await update.message.reply_text("📰 실시간 속보를 가져오는 중...")

    breaking_items = get_breaking_news(chat_id)

    # Issue #16: 언론사 필터링 적용
    breaking_items = filter_by_source(breaking_items, chat_id)

    if not breaking_items:
        await update.message.reply_text("현재 스코어링 기준에 맞는 속보가 없습니다.")
        return

    # send_news_with_images와 동일한 방식으로 전송
    if breaking_items:
        recent_articles[chat_id] = breaking_items[0]

    for item in breaking_items:
        title = item['title']
        url = item['url']
        image_url = item.get('image_url', '')
        score = item.get('score', 0)

        caption = f"[{score:+}] {title}\n{url}"

        sent_message = None
        try:
            if image_url and image_url.startswith('http'):
                sent_message = await update.message.reply_photo(
                    photo=image_url,
                    caption=caption
                )
            else:
                sent_message = await update.message.reply_text(
                    text=caption,
                    disable_web_page_preview=False
                )
        except Exception as e:
            print(f"속보 전송 실패: {e}")
            sent_message = await update.message.reply_text(
                text=caption,
                disable_web_page_preview=True
            )

        # 메시지 ID를 기사에 매핑 (이모지 리액션 피드백용)
        if sent_message:
            message_to_article[sent_message.message_id] = item

        await asyncio.sleep(0.3)


async def breaking_auto_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """속보 자동 알림 시작"""
    chat_id = update.effective_chat.id

    old_task = breaking_tasks.get(chat_id)
    if old_task is not None and not old_task.done():
        old_task.cancel()

    task = context.application.create_task(
        breaking_auto_loop(chat_id, context.bot)
    )
    breaking_tasks[chat_id] = task

    await update.message.reply_text(
        "⏱ 속보 자동 알림 시작 (5분 간격)\n"
        "💡 새 속보가 있을 때만 알림이 옵니다."
    )


async def breaking_auto_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """속보 자동 알림 중지"""
    chat_id = update.effective_chat.id

    task = breaking_tasks.pop(chat_id, None)
    if task is None or task.done():
        await update.message.reply_text("현재 속보 자동 알림이 켜져 있지 않습니다.")
        return

    task.cancel()
    await update.message.reply_text("⏹ 속보 자동 알림을 중지했습니다.")


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


# ---------------- 스코어링 설정 (블랙리스트/화이트리스트) ----------------

async def whitelist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """화이트리스트 키워드 추가"""
    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        await update.message.reply_text(
            "사용법: /whitelist 키워드\n"
            "예: /whitelist 비트코인\n\n"
            "이 키워드를 포함한 뉴스만 표시됩니다."
        )
        return

    keyword = " ".join(args).strip()
    db = get_db()

    if db.add_whitelist_keyword(chat_id, keyword):
        settings = db.get_user_scoring_settings(chat_id)
        whitelist = settings["whitelist_keywords"]
        await update.message.reply_text(
            f"✅ '{keyword}' 화이트리스트에 추가\n\n"
            f"현재 화이트리스트 ({len(whitelist)}):\n" +
            "\n".join(f"• {kw}" for kw in whitelist)
        )
    else:
        await update.message.reply_text(f"'{keyword}'는 이미 화이트리스트에 있습니다.")


async def remove_whitelist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """화이트리스트 키워드 제거"""
    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        await update.message.reply_text("사용법: /remove_whitelist 키워드")
        return

    keyword = " ".join(args).strip()
    db = get_db()

    if db.remove_whitelist_keyword(chat_id, keyword):
        await update.message.reply_text(f"✅ '{keyword}' 화이트리스트에서 제거")
    else:
        await update.message.reply_text(f"'{keyword}'는 화이트리스트에 없습니다.")


async def blacklist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """블랙리스트 키워드 추가"""
    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        await update.message.reply_text(
            "사용법: /blacklist 키워드\n"
            "예: /blacklist 광고\n\n"
            "이 키워드를 포함한 뉴스는 무조건 제외됩니다."
        )
        return

    keyword = " ".join(args).strip()
    db = get_db()

    if db.add_blacklist_keyword(chat_id, keyword):
        settings = db.get_user_scoring_settings(chat_id)
        blacklist = settings["blacklist_keywords"]
        await update.message.reply_text(
            f"🚫 '{keyword}' 블랙리스트에 추가\n\n"
            f"현재 블랙리스트 ({len(blacklist)}):\n" +
            "\n".join(f"• {kw}" for kw in blacklist)
        )
    else:
        await update.message.reply_text(f"'{keyword}'는 이미 블랙리스트에 있습니다.")


async def remove_blacklist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """블랙리스트 키워드 제거"""
    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        await update.message.reply_text("사용법: /remove_blacklist 키워드")
        return

    keyword = " ".join(args).strip()
    db = get_db()

    if db.remove_blacklist_keyword(chat_id, keyword):
        await update.message.reply_text(f"✅ '{keyword}' 블랙리스트에서 제거")
    else:
        await update.message.reply_text(f"'{keyword}'는 블랙리스트에 없습니다.")


# ---------------- 테마 스코어링 ----------------

async def theme_add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, days: int):
    """테마 키워드 추가 (기간 제한)"""
    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        await update.message.reply_text(
            f"사용법: /{days}d_add 키워드\n"
            f"예: /{days}d_add AI규제\n\n"
            f"{days}일간 해당 키워드 관련 뉴스에 +5점이 부여됩니다."
        )
        return

    keyword = " ".join(args).strip()
    db = get_db()

    db.add_theme_keyword(chat_id, keyword, days=days, score=5)
    await update.message.reply_text(
        f"⏰ '{keyword}' 테마 키워드 추가\n"
        f"• 기간: {days}일\n"
        f"• 점수: +5점\n\n"
        f"{days}일 동안 '{keyword}' 관련 뉴스에 +5점이 부여됩니다."
    )


async def theme_5d_add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await theme_add_cmd(update, context, 5)


async def theme_20d_add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await theme_add_cmd(update, context, 20)


async def theme_45d_add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await theme_add_cmd(update, context, 45)


async def theme_60d_add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await theme_add_cmd(update, context, 60)


async def theme_120d_add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await theme_add_cmd(update, context, 120)


async def theme_225d_add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await theme_add_cmd(update, context, 225)


async def themes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """현재 활성화된 테마 키워드 목록 확인"""
    from datetime import datetime, timezone

    chat_id = update.effective_chat.id
    db = get_db()

    settings = db.get_user_scoring_settings(chat_id)
    theme_keywords = settings["theme_keywords"]

    if not theme_keywords:
        await update.message.reply_text(
            "⏰ 현재 활성화된 테마 키워드가 없습니다.\n\n"
            "테마 키워드 추가 방법:\n"
            "• /5d_add 키워드   : 5일간 +5점\n"
            "• /20d_add 키워드  : 20일간 +5점\n"
            "• /45d_add 키워드  : 45일간 +5점\n"
            "• /60d_add 키워드  : 60일간 +5점\n"
            "• /120d_add 키워드 : 120일간 +5점\n"
            "• /225d_add 키워드 : 225일간 +5점"
        )
        return

    # 만료되지 않은 테마만 필터링
    now = datetime.now(timezone.utc)
    active_themes = []
    expired_themes = []

    for keyword, info in theme_keywords.items():
        expire_at = datetime.fromisoformat(info["expire_at"])
        score = info["score"]

        if expire_at > now:
            # 남은 일수 계산
            days_left = (expire_at - now).days
            active_themes.append((keyword, score, days_left, expire_at))
        else:
            expired_themes.append(keyword)

    # 메시지 작성
    msg_parts = ["⏰ 활성화된 테마 키워드\n", "━━━━━━━━━━━━━━━━━━━━━━"]

    if active_themes:
        # 남은 일수로 정렬 (적게 남은 순)
        active_themes.sort(key=lambda x: x[2])

        for keyword, score, days_left, expire_at in active_themes:
            expire_date = expire_at.strftime("%Y-%m-%d")
            msg_parts.append(
                f"• {keyword}\n"
                f"  └ 점수: +{score}점\n"
                f"  └ 남은 기간: {days_left}일 (만료: {expire_date})"
            )

    if expired_themes:
        msg_parts.append("\n━━━━━━━━━━━━━━━━━━━━━━")
        msg_parts.append("⏱ 만료된 테마 (자동 제거됨)")
        msg_parts.append("━━━━━━━━━━━━━━━━━━━━━━")
        for keyword in expired_themes:
            msg_parts.append(f"• {keyword}")

    if not active_themes and not expired_themes:
        msg_parts.append("\n현재 활성화된 테마가 없습니다.")

    await update.message.reply_text("\n".join(msg_parts))


# ---------------- 분류별 스코어링 ----------------

# 분류 매핑
SECTOR_MAP = {
    "거시경제": "거시경제",
    "거시": "거시경제",
    "경제": "거시경제",
    "사회정책": "사회정책",
    "사회": "사회정책",
    "정책": "사회정책",
    "금융": "금융",
    "산업/기술": "산업/기술",
    "산업": "산업/기술",
    "기술": "산업/기술",
    "문화/생활": "문화/생활",
    "문화": "문화/생활",
    "생활": "문화/생활",
}


async def class_add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """분류별 스코어 설정"""
    chat_id = update.effective_chat.id
    args = context.args

    if len(args) < 2:
        await update.message.reply_text(
            "사용법: /class_add 분류명 점수\n\n"
            "분류:\n"
            "• 거시경제 (또는 경제, 거시)\n"
            "• 사회정책 (또는 사회, 정책)\n"
            "• 금융\n"
            "• 산업/기술 (또는 산업, 기술)\n"
            "• 문화/생활 (또는 문화, 생활)\n\n"
            "예:\n"
            "• /class_add 금융 3\n"
            "• /class_add 문화/생활 -2"
        )
        return

    sector_input = args[0].strip()
    try:
        score = int(args[1])
    except ValueError:
        await update.message.reply_text("점수는 숫자로 입력해주세요.\n예: /class_add 금융 3")
        return

    # 분류 매핑
    sector = SECTOR_MAP.get(sector_input)
    if not sector:
        await update.message.reply_text(
            f"'{sector_input}'는 유효한 분류가 아닙니다.\n\n"
            "유효한 분류:\n"
            "• 거시경제, 사회정책, 금융, 산업/기술, 문화/생활"
        )
        return

    db = get_db()
    db.set_sector_score(chat_id, sector, score)

    settings = db.get_user_scoring_settings(chat_id)
    sector_scores = settings["sector_scores"]

    await update.message.reply_text(
        f"📂 '{sector}' 분류 점수 설정: {score:+}점\n\n"
        "현재 분류별 점수:\n" +
        "\n".join(f"• {s}: {sc:+}점" for s, sc in sector_scores.items())
    )


# ---------------- 최소 스코어 제한 ----------------

async def exclude_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """최소 스코어 제한 설정"""
    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        await update.message.reply_text(
            "사용법: /exclude 최소점수\n\n"
            "예:\n"
            "• /exclude 2 (2점 미만 뉴스 제외)\n"
            "• /exclude 0 (0점 미만 뉴스 제외)\n"
            "• /exclude -1 (-1점 미만 뉴스 제외)"
        )
        return

    try:
        min_score = int(args[0])
    except ValueError:
        await update.message.reply_text("점수는 숫자로 입력해주세요.\n예: /exclude 2")
        return

    db = get_db()
    db.set_exclude_min_score(chat_id, min_score)

    await update.message.reply_text(
        f"🎯 최소 스코어 제한 설정: {min_score}점\n\n"
        f"{min_score}점 미만의 뉴스는 표시되지 않습니다."
    )


async def scores_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """전체 스코어링 규칙 확인"""
    chat_id = update.effective_chat.id
    db = get_db()

    # 스코어링 설정 가져오기
    settings = db.get_user_scoring_settings(chat_id)
    keyword_scores = db.get_keywords_with_scores(chat_id)

    from datetime import datetime, timezone

    msg_parts = []
    msg_parts.append("📊 현재 스코어링 규칙\n")
    msg_parts.append("━━━━━━━━━━━━━━━━━━━━━━")

    # 1. 기본 키워드
    if keyword_scores:
        msg_parts.append(f"\n🔑 기본 키워드 ({len(keyword_scores)}):")
        for kw, score in keyword_scores.items():
            msg_parts.append(f"  • {kw}: {score:+}점")
    else:
        msg_parts.append("\n🔑 기본 키워드: 없음")

    # 2. 화이트리스트
    whitelist = settings["whitelist_keywords"]
    if whitelist:
        msg_parts.append(f"\n⚪ 화이트리스트 ({len(whitelist)}):")
        for kw in whitelist:
            msg_parts.append(f"  • {kw}")

    # 3. 블랙리스트
    blacklist = settings["blacklist_keywords"]
    if blacklist:
        msg_parts.append(f"\n⚫ 블랙리스트 ({len(blacklist)}):")
        for kw in blacklist:
            msg_parts.append(f"  • {kw}")

    # 4. 테마 키워드 (기간 제한)
    theme_keywords = settings["theme_keywords"]
    if theme_keywords:
        now = datetime.now(timezone.utc)
        active_themes = []
        expired_themes = []

        for kw, theme_data in theme_keywords.items():
            expire_str = theme_data.get("expire_at", "")
            score = theme_data.get("score", 5)

            try:
                expire_date = datetime.fromisoformat(expire_str)
                days_left = (expire_date - now).days

                if now < expire_date:
                    active_themes.append(f"  • {kw} ({score:+}점, {days_left}일 남음)")
                else:
                    expired_themes.append(f"  • {kw} (만료됨)")
            except (ValueError, AttributeError):
                expired_themes.append(f"  • {kw} (만료됨)")

        if active_themes:
            msg_parts.append(f"\n⏰ 테마 키워드 ({len(active_themes)}):")
            msg_parts.extend(active_themes)

        if expired_themes:
            msg_parts.append(f"\n⏰ 만료된 테마 ({len(expired_themes)}):")
            msg_parts.extend(expired_themes)

    # 5. 분류별 점수
    sector_scores = settings["sector_scores"]
    if sector_scores:
        msg_parts.append(f"\n📂 분류별 점수:")
        for sector, score in sector_scores.items():
            msg_parts.append(f"  • {sector}: {score:+}점")

    # 6. 최소 스코어 제한
    exclude_min_score = settings["exclude_min_score"]
    if exclude_min_score is not None:
        msg_parts.append(f"\n🎯 최소 스코어 제한: {exclude_min_score}점")

    msg_parts.append("\n━━━━━━━━━━━━━━━━━━━━━━")

    # 메시지 전송
    await update.message.reply_text("\n".join(msg_parts))


# ---------------- 유저 피드백 ----------------

# 최근 전송한 기사를 임시 저장 (chat_id -> article)
recent_articles: dict[int, dict] = {}

# 메시지 ID를 기사 정보에 매핑 (message_id -> article)
message_to_article: dict[int, dict] = {}


async def like_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """가장 최근 기사에 좋아요"""
    chat_id = update.effective_chat.id

    # 최근 기사 확인
    if chat_id not in recent_articles:
        await update.message.reply_text(
            "최근 받은 기사가 없습니다.\n"
            "먼저 뉴스를 검색하거나 /scan, /rss_now를 실행해주세요."
        )
        return

    article = recent_articles[chat_id]
    article_url = article.get('url', '')
    article_title = article.get('title', '제목 없음')

    # 피드백 저장
    from app.database.db_manager import get_db
    import hashlib

    db = get_db()
    article_id = hashlib.md5(article_url.encode()).hexdigest()

    db.add_feedback(
        chat_id=chat_id,
        article_id=article_id,
        feedback_type="like",
        feedback_value=1,
        comment=""
    )

    await update.message.reply_text(
        f"👍 피드백 감사합니다!\n\n"
        f"'{article_title[:50]}...' 기사를 좋아요 했습니다."
    )


async def dislike_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """가장 최근 기사에 싫어요"""
    chat_id = update.effective_chat.id
    args = context.args

    # 이유 (선택사항)
    reason = " ".join(args).strip() if args else ""

    # 최근 기사 확인
    if chat_id not in recent_articles:
        await update.message.reply_text(
            "최근 받은 기사가 없습니다.\n"
            "먼저 뉴스를 검색하거나 /scan, /rss_now를 실행해주세요."
        )
        return

    article = recent_articles[chat_id]
    article_url = article.get('url', '')
    article_title = article.get('title', '제목 없음')

    # 피드백 저장
    from app.database.db_manager import get_db
    import hashlib

    db = get_db()
    article_id = hashlib.md5(article_url.encode()).hexdigest()

    db.add_feedback(
        chat_id=chat_id,
        article_id=article_id,
        feedback_type="dislike",
        feedback_value=-1,
        comment=reason
    )

    msg = f"👎 피드백 감사합니다!\n\n'{article_title[:50]}...' 기사를 싫어요 했습니다."
    if reason:
        msg += f"\n\n이유: {reason}"

    await update.message.reply_text(msg)


async def feedback_stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """내 피드백 통계 보기"""
    chat_id = update.effective_chat.id

    from app.database.db_manager import get_db
    db = get_db()

    # 전체 피드백 가져오기
    all_feedback = db.get_user_feedback(chat_id)

    if not all_feedback:
        await update.message.reply_text(
            "아직 피드백이 없습니다.\n\n"
            "/like 또는 /dislike 명령어로 기사에 피드백을 남겨보세요!"
        )
        return

    # 통계 계산
    likes = [f for f in all_feedback if f['feedback_type'] == 'like']
    dislikes = [f for f in all_feedback if f['feedback_type'] == 'dislike']

    msg_parts = []
    msg_parts.append("📊 내 피드백 통계\n")
    msg_parts.append("━━━━━━━━━━━━━━━━━━━━━━")
    msg_parts.append(f"\n👍 좋아요: {len(likes)}개")
    msg_parts.append(f"👎 싫어요: {len(dislikes)}개")
    msg_parts.append(f"📝 전체: {len(all_feedback)}개")

    # 최근 피드백 5개
    recent = sorted(all_feedback, key=lambda x: x['created_at'], reverse=True)[:5]

    if recent:
        msg_parts.append("\n━━━━━━━━━━━━━━━━━━━━━━")
        msg_parts.append("\n📋 최근 피드백:")

        for fb in recent:
            icon = "👍" if fb['feedback_type'] == 'like' else "👎"
            comment = f" - {fb['comment']}" if fb['comment'] else ""
            msg_parts.append(f"{icon} {fb['created_at'][:10]}{comment}")

    msg_parts.append("\n━━━━━━━━━━━━━━━━━━━━━━")

    await update.message.reply_text("\n".join(msg_parts))


async def reaction_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    이모지 리액션 기반 피드백 처리
    사용자가 봇 메시지에 👍 또는 👎 리액션을 달면 자동으로 피드백 저장
    """
    reaction: telegram.MessageReactionUpdated = update.message_reaction

    if not reaction or not reaction.new_reaction:
        return

    message_id = reaction.message_id
    chat_id = reaction.chat.id

    # 해당 메시지가 기사 메시지인지 확인
    if message_id not in message_to_article:
        return

    article = message_to_article[message_id]
    article_url = article.get('url', '')
    article_title = article.get('title', '제목 없음')

    # 새로운 리액션 확인
    new_reactions = reaction.new_reaction

    # 👍 또는 👎 리액션이 있는지 확인
    feedback_type = None
    feedback_value = None

    for reaction_item in new_reactions:
        emoji = getattr(reaction_item, 'emoji', None)
        if emoji == '👍':
            feedback_type = 'like'
            feedback_value = 1
            break
        elif emoji == '👎':
            feedback_type = 'dislike'
            feedback_value = -1
            break

    if not feedback_type:
        return

    # 피드백 저장
    from app.database.db_manager import get_db
    import hashlib

    db = get_db()
    article_id = hashlib.md5(article_url.encode()).hexdigest()

    db.add_feedback(
        chat_id=chat_id,
        article_id=article_id,
        feedback_type=feedback_type,
        feedback_value=feedback_value,
        comment=""
    )

    # 확인 메시지 (선택사항 - 조용히 처리하고 싶으면 이 부분 제거)
    # icon = "👍" if feedback_type == "like" else "👎"
    # await context.bot.send_message(
    #     chat_id=chat_id,
    #     text=f"{icon} 피드백 감사합니다!"
    # )


# ---------------- main ----------------

def main():
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .job_queue(None)
        .build()
    )

    # 기본 안내
    app.add_handler(CommandHandler("intro", intro))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("scoring_help", scoring_help_cmd))
    app.add_handler(CommandHandler("breaking_help", breaking_help_cmd))

    # 관심 키워드 관련
    app.add_handler(CommandHandler("add", add_cmd))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("del", del_cmd))
    app.add_handler(CommandHandler("scan", scan_cmd))

    # 뉴스 알림 (RSS 기반)
    app.add_handler(CommandHandler("start", start_news))
    app.add_handler(CommandHandler("stop", stop_news))
    app.add_handler(CommandHandler("rss_now", rss_now))

    # 속보 관련
    app.add_handler(CommandHandler("breaking_now", breaking_now))
    app.add_handler(CommandHandler("breaking_auto_on", breaking_auto_on))
    app.add_handler(CommandHandler("breaking_auto_off", breaking_auto_off))

    # 언론사 필터링 (Issue #16)
    app.add_handler(CommandHandler("block", block_cmd))
    app.add_handler(CommandHandler("allow", allow_cmd))
    app.add_handler(CommandHandler("sources", sources_cmd))

    # 스코어링 설정 (블랙리스트/화이트리스트)
    app.add_handler(CommandHandler("whitelist", whitelist_cmd))
    app.add_handler(CommandHandler("remove_whitelist", remove_whitelist_cmd))
    app.add_handler(CommandHandler("blacklist", blacklist_cmd))
    app.add_handler(CommandHandler("remove_blacklist", remove_blacklist_cmd))

    # 테마 스코어링
    app.add_handler(CommandHandler("5d_add", theme_5d_add_cmd))
    app.add_handler(CommandHandler("20d_add", theme_20d_add_cmd))
    app.add_handler(CommandHandler("45d_add", theme_45d_add_cmd))
    app.add_handler(CommandHandler("60d_add", theme_60d_add_cmd))
    app.add_handler(CommandHandler("120d_add", theme_120d_add_cmd))
    app.add_handler(CommandHandler("225d_add", theme_225d_add_cmd))
    app.add_handler(CommandHandler("themes", themes_cmd))

    # 분류별 스코어링
    app.add_handler(CommandHandler("class_add", class_add_cmd))

    # 최소 스코어 제한
    app.add_handler(CommandHandler("exclude", exclude_cmd))

    # 스코어링 규칙 확인
    app.add_handler(CommandHandler("scores", scores_cmd))

    # 유저 피드백
    app.add_handler(CommandHandler("like", like_cmd))
    app.add_handler(CommandHandler("dislike", dislike_cmd))
    app.add_handler(CommandHandler("feedback", feedback_stats_cmd))

    # 이모지 리액션 피드백 (동적 로드)
    if MessageReactionHandler:
        app.add_handler(MessageReactionHandler(reaction_handler))
    else:
        print("⚠️  MessageReactionHandler를 사용할 수 없습니다. 이모지 리액션 피드백이 비활성화됩니다.")

    # 일반 텍스트 → 뉴스 검색
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling()


if __name__ == "__main__":
    main()
