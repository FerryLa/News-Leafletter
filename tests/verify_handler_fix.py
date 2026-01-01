#!/usr/bin/env python3
"""MessageReactionHandler 로딩 검증 스크립트"""

def test_handler_loading():
    """main() 함수와 동일한 방식으로 핸들러 로딩 테스트"""

    print("=" * 60)
    print("MessageReactionHandler 로딩 검증")
    print("=" * 60)

    # bot.py의 main() 함수와 동일한 코드
    try:
        from telegram.ext import MessageReactionHandler
        print("\nSUCCESS: MessageReactionHandler 로드 성공!")
        print(f"  클래스: {MessageReactionHandler}")
        print(f"  모듈: {MessageReactionHandler.__module__}")

        # 핸들러 인스턴스 생성 테스트
        async def dummy_handler(update, context):
            pass

        handler = MessageReactionHandler(dummy_handler)
        print(f"\nSUCCESS: 핸들러 인스턴스 생성 성공!")
        print(f"  타입: {type(handler).__name__}")

        print("\n" + "=" * 60)
        print("이모지 리액션 기능이 정상 작동합니다!")
        print("=" * 60)

        return True

    except (ImportError, AttributeError) as e:
        print(f"\nFAILED: MessageReactionHandler 로드 실패: {e}")
        print("\n이모지 리액션 피드백 기능을 사용할 수 없습니다.")
        print("기존 /like, /dislike 명령어는 정상 작동합니다.")
        return False

if __name__ == "__main__":
    success = test_handler_loading()
    exit(0 if success else 1)
