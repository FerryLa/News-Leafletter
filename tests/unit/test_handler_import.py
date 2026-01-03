#!/usr/bin/env python3
"""MessageReactionHandler 동적 로딩 테스트"""

import importlib

def test_handler_import():
    """MessageReactionHandler를 동적으로 로드할 수 있는지 테스트"""

    print("=" * 60)
    print("MessageReactionHandler 동적 로딩 테스트")
    print("=" * 60)

    # 1. importlib를 사용한 동적 로딩
    print("\n[1] importlib.import_module()로 telegram.ext 로드...")
    telegram_ext = importlib.import_module('telegram.ext')
    print("    ✓ 모듈 로드 성공")

    # 2. getattr로 MessageReactionHandler 접근
    print("\n[2] getattr()로 MessageReactionHandler 접근...")
    MessageReactionHandler = getattr(telegram_ext, 'MessageReactionHandler', None)

    if MessageReactionHandler:
        print("    ✓ MessageReactionHandler 로드 성공")
        print(f"    - Type: {type(MessageReactionHandler)}")
        print(f"    - Module: {MessageReactionHandler.__module__}")
        print(f"    - Name: {MessageReactionHandler.__name__}")
    else:
        print("    ✗ MessageReactionHandler를 찾을 수 없습니다")
        return False

    # 3. 핸들러 생성 가능 여부 테스트
    print("\n[3] 핸들러 생성 테스트...")
    try:
        async def dummy_callback(update, context):
            pass

        handler = MessageReactionHandler(dummy_callback)
        print("    ✓ 핸들러 인스턴스 생성 성공")
        print(f"    - Handler type: {type(handler)}")
    except Exception as e:
        print(f"    ✗ 핸들러 생성 실패: {e}")
        return False

    print("\n" + "=" * 60)
    print("✓ 모든 테스트 통과!")
    print("=" * 60)
    print("\n다음 단계:")
    print("1. bot.py 실행 (python bot.py)")
    print("2. 텔레그램에서 기사 검색 또는 /scan 실행")
    print("3. 받은 기사 메시지에 👍 또는 👎 이모지 리액션 추가")
    print("4. /feedback 명령어로 피드백 저장 확인")
    print("=" * 60)

    return True

if __name__ == "__main__":
    test_handler_import()
