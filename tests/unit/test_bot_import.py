#!/usr/bin/env python3
"""bot.py의 import 방식이 제대로 작동하는지 테스트"""

print("=" * 60)
print("bot.py import 테스트")
print("=" * 60)

# bot.py와 동일한 방식으로 import
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
    print("\n✓ MessageReactionHandler 로드 성공!")
    print(f"  Type: {type(MessageReactionHandler)}")
    print(f"  Module: {MessageReactionHandler.__module__}")

    # None 체크
    if MessageReactionHandler:
        print("\n✓ MessageReactionHandler는 None이 아닙니다")
        print("  이모지 리액션 기능이 활성화됩니다")
    else:
        print("\n✗ MessageReactionHandler가 None입니다")

except (ImportError, AttributeError) as e:
    print(f"\n✗ MessageReactionHandler 로드 실패: {e}")
    MessageReactionHandler = None
    print("  이모지 리액션 기능이 비활성화됩니다")

print("\n" + "=" * 60)
if MessageReactionHandler:
    print("SUCCESS: bot.py에서 이모지 리액션 기능을 사용할 수 있습니다!")
else:
    print("FAILED: bot.py에서 이모지 리액션 기능을 사용할 수 없습니다")
print("=" * 60)
