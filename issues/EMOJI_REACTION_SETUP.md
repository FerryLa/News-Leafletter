# 이모지 리액션 피드백 기능 설정 가이드

## 최종 해결 방법

python-telegram-bot v22.5에서 MessageReactionHandler를 사용하려면 **파일 상단(모듈 레벨)**에서 import해야 합니다.

### bot.py 수정 내용

**Lines 15-19 (파일 상단)**:
```python
# MessageReactionHandler 로드 (선택적)
try:
    from telegram.ext import MessageReactionHandler
except (ImportError, AttributeError):
    MessageReactionHandler = None
```

**Lines 1187-1190 (main() 함수 내)**:
```python
# 이모지 리액션 피드백
if MessageReactionHandler:
    app.add_handler(MessageReactionHandler(reaction_handler))
else:
    print("⚠️  MessageReactionHandler를 사용할 수 없습니다. 이모지 리액션 피드백이 비활성화됩니다.")
```

## 실패했던 방법들

1. ❌ **main() 함수 내부에서 import**: 로컬 스코프 문제로 None 반환
2. ❌ **내부 모듈 직접 import** (`from telegram.ext._handlers.messagereactionhandler import ...`): 모듈 경로 문제
3. ❌ **importlib 동적 로딩**: 모듈 캐싱 문제
4. ✅ **모듈 레벨에서 import**: 정상 작동!

## 테스트 방법

### 1. Import 테스트
```bash
python test_bot_import.py
```

예상 출력:
```
============================================================
bot.py import 테스트
============================================================

✓ MessageReactionHandler 로드 성공!
  Type: <class 'abc.ABCMeta'>
  Module: telegram.ext._handlers.messagereactionhandler

✓ MessageReactionHandler는 None이 아닙니다
  이모지 리액션 기능이 활성화됩니다

============================================================
SUCCESS: bot.py에서 이모지 리액션 기능을 사용할 수 있습니다!
============================================================
```

### 2. 봇 실행
```bash
python bot.py
```

**경고 메시지가 나타나지 않으면 성공**입니다:
- ✅ 정상: 봇이 시작되고 경고 없음
- ❌ 실패: `⚠️ MessageReactionHandler를 사용할 수 없습니다...` 메시지 표시

### 3. 실제 기능 테스트
1. 텔레그램에서 봇과 대화
2. 키워드 검색 또는 `/scan` 실행
3. 받은 기사 메시지에 👍 또는 👎 리액션 추가
4. `/feedback` 명령어로 피드백 저장 확인

## 핵심 개념

### 왜 모듈 레벨에서 import해야 하는가?

Python에서 함수 내부의 `import` 문은 로컬 스코프를 가집니다. main() 함수 내에서 import한 MessageReactionHandler는 함수가 종료되면 사라지거나, 내부 최적화로 인해 예상과 다르게 동작할 수 있습니다.

반면 **모듈 레벨(파일 상단)**에서 import하면:
- 모듈이 로드될 때 한 번만 실행됨
- 전역 스코프에서 접근 가능
- 예측 가능한 동작

### try-except가 필요한 이유

python-telegram-bot의 버전이나 설치 상태에 따라 MessageReactionHandler를 import하지 못할 수 있습니다. try-except를 사용하면:
- Import 실패 시 봇이 중단되지 않음
- 다른 기능(`/like`, `/dislike`)은 정상 작동
- 사용자에게 명확한 경고 메시지 제공

## 구현된 기능

### reaction_handler 함수 (Lines 1127-1189)
```python
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

    # 👍/👎 리액션 확인 및 DB 저장
    # ...
```

### 메시지 ID 매핑 (Lines 415-416, 503-504)
```python
# send_news_with_images 함수
if sent_message:
    message_to_article[sent_message.message_id] = item

# rss_auto_loop 함수
if sent_message:
    message_to_article[sent_message.message_id] = item
```

## 참고사항

### 봇 권한 설정
텔레그램 봇이 메시지 리액션을 받으려면 BotFather에서 권한 설정이 필요할 수 있습니다:

1. BotFather와 대화
2. `/mybots` → 봇 선택 → `Bot Settings` → `Group Privacy` → `Turn off`

### 메모리 관리
`message_to_article` 딕셔너리는 메모리에 계속 쌓입니다. 장기 실행 시 주기적으로 오래된 항목을 정리하는 로직이 필요할 수 있습니다.

## 트러블슈팅

### Q: 경고 메시지가 계속 나타납니다
**A**: 다음을 확인하세요:
1. python-telegram-bot이 올바르게 설치되었는지: `pip list | grep python-telegram-bot`
2. 버전이 22.5인지: `python -c "import telegram; print(telegram.__version__)"`
3. test_bot_import.py 테스트 결과

### Q: 리액션을 달아도 피드백이 저장되지 않습니다
**A**: 다음을 확인하세요:
1. 봇이 경고 없이 시작되었는지
2. BotFather에서 Group Privacy 설정
3. 봇이 해당 채팅방의 관리자인지
4. 기사 메시지가 봇이 전송한 메시지인지 (다른 메시지에는 반응하지 않음)

### Q: /feedback 명령어는 작동하지만 이모지 리액션이 안됩니다
**A**: MessageReactionHandler가 로드되지 않았을 가능성이 높습니다. 봇 시작 시 경고 메시지를 확인하세요.

## 완료 일시
2025-12-31
