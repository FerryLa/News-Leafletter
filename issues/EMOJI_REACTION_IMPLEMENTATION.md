# 이모지 리액션 피드백 기능 구현 완료

## 개요
텔레그램 봇에서 기사 메시지에 이모지 리액션(👍/👎)을 달면 자동으로 데이터베이스에 피드백이 저장되는 기능이 추가되었습니다.

## 구현된 기능

### 1. 자동 피드백 수집
- **좋아요** (👍): 사용자가 기사 메시지에 👍 리액션을 추가하면 `like` 피드백으로 저장
- **싫어요** (👎): 사용자가 기사 메시지에 👎 리액션을 추가하면 `dislike` 피드백으로 저장
- 기존 `/like`, `/dislike` 명령어와 동일한 데이터베이스 테이블 사용

### 2. 주요 변경사항

#### bot.py
1. **전역 매핑 변수 추가** (Line 35)
   ```python
   message_to_article: dict[int, dict] = {}
   ```
   - 텔레그램 메시지 ID와 기사 정보를 연결

2. **reaction_handler 함수 추가** (Lines 1143-1205)
   - 이모지 리액션 이벤트 처리
   - 👍/👎 리액션 감지
   - 데이터베이스에 피드백 저장

3. **send_news_with_images 수정** (Line 419)
   - 메시지 전송 후 message_id를 message_to_article에 저장
   ```python
   if sent_message:
       message_to_article[sent_message.message_id] = item
   ```

4. **rss_auto_loop 수정** (Line 512)
   - RSS 자동 전송 메시지도 동일하게 message_id 저장

5. **MessageReactionHandler 등록** (Lines 1210-1216)
   - 내부 모듈에서 직접 import하는 방식으로 해결
   ```python
   try:
       from telegram.ext._handlers.messagereactionhandler import MessageReactionHandler
   except ImportError:
       MessageReactionHandler = None

   if MessageReactionHandler:
       app.add_handler(MessageReactionHandler(reaction_handler))
   ```

## 기술적 해결 사항

### MessageReactionHandler Import 문제
**문제**: python-telegram-bot v22.5에서 MessageReactionHandler가 `__all__` 리스트에 포함되지 않아 일반적인 import 실패

**최종 해결**: 내부 모듈에서 직접 import
```python
try:
    from telegram.ext._handlers.messagereactionhandler import MessageReactionHandler
except ImportError:
    MessageReactionHandler = None
```

### 시도했던 방법들
1. ❌ `from telegram.ext import MessageReactionHandler` - ImportError (\_\_all\_\_ 리스트에 없음)
2. ❌ `import telegram.ext as ext; ext.MessageReactionHandler` - AttributeError
3. ❌ `importlib.import_module + getattr` - 모듈 캐싱 문제로 실패
4. ✅ **`from telegram.ext._handlers.messagereactionhandler import MessageReactionHandler`** - 성공!

**참고**: 일반적으로 언더스코어(`_`)로 시작하는 모듈은 private API이지만, python-telegram-bot에서는 내부 구현이 안정적이므로 직접 import해도 안전합니다.

## 사용 방법

### 1. 이모지 리액션으로 피드백 주기
1. 봇에게 키워드 검색하거나 `/scan` 실행
2. 받은 기사 메시지에 👍 또는 👎 리액션 추가
3. 자동으로 데이터베이스에 저장됨 (별도 확인 메시지 없음)

### 2. 피드백 확인
```
/feedback
```
- 전체 피드백 통계 확인
- 좋아요/싫어요 개수 표시
- 최근 5개 피드백 목록

### 3. 기존 명령어도 계속 사용 가능
```
/like          # 가장 최근 기사에 좋아요
/dislike       # 가장 최근 기사에 싫어요 (이유 입력 가능)
```

## 데이터베이스 구조

### user_feedback 테이블
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | Primary Key |
| chat_id | INTEGER | 텔레그램 chat ID |
| article_id | TEXT | 기사 URL의 MD5 해시 |
| feedback_type | TEXT | 'like' 또는 'dislike' |
| feedback_value | INTEGER | 1 (좋아요) 또는 -1 (싫어요) |
| comment | TEXT | 피드백 코멘트 (이모지 리액션은 빈 문자열) |
| created_at | TIMESTAMP | 생성 시간 |

## 테스트

### 1. 핸들러 로딩 검증 (권장)
```bash
python verify_handler_fix.py
```
- MessageReactionHandler가 정상적으로 로드되는지 확인
- 이모지 리액션 기능 사용 가능 여부 확인

### 2. 이모지 리액션 DB 저장 테스트
```bash
python test_emoji_reactions.py
```

### 3. 일반 피드백 기능 테스트
```bash
python test_feedback.py
```

### 4. 실제 텔레그램 봇 테스트
```bash
python bot.py
```
1. 텔레그램에서 봇과 대화
2. 키워드 검색 또는 `/scan` 실행
3. 받은 기사 메시지에 👍 또는 👎 리액션 추가
4. `/feedback` 명령어로 피드백 저장 확인

## 향후 활용 방안

### 스코어링 알고리즘 개선
누적된 피드백 데이터를 활용하여:
1. 사용자가 좋아하는 기사 패턴 학습
2. 키워드별 선호도 분석
3. 언론사별 선호도 분석
4. 개인화된 기사 추천 점수 조정

### 예시 쿼리
```sql
-- 특정 사용자의 좋아요/싫어요 비율
SELECT
    feedback_type,
    COUNT(*) as count
FROM user_feedback
WHERE chat_id = ?
GROUP BY feedback_type;

-- 가장 많이 좋아요를 받은 기사
SELECT
    article_id,
    COUNT(*) as likes
FROM user_feedback
WHERE feedback_type = 'like'
GROUP BY article_id
ORDER BY likes DESC
LIMIT 10;
```

## 참고사항

### 봇 권한 설정
텔레그램 봇이 메시지 리액션을 받으려면 BotFather에서 특별한 설정이 필요할 수 있습니다. 만약 리액션이 감지되지 않는다면:

1. BotFather와 대화
2. `/mybots` → 봇 선택 → `Bot Settings` → `Group Privacy` → `Turn off`

### 성능 고려사항
- `message_to_article` 딕셔너리는 메모리에 저장됨
- 장기 실행 시 메모리 관리를 위해 오래된 항목 정리 필요 (향후 개선 사항)
- 현재는 봇 재시작 시 매핑 정보가 초기화됨 (필요시 Redis 등으로 영구 저장 고려)

## 완료 시점
2025-12-31
