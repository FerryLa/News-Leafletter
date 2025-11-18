# storage.py
import json
from pathlib import Path

# 프로젝트 루트 기준 파일 이름
DATA_FILE = Path("watchlist.json")


def _load_data() -> dict:
    if not DATA_FILE.exists():
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # 깨졌으면 그냥 초기화
        return {}


def _save_data(data: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_keywords(chat_id: int) -> list[str]:
    data = _load_data()
    return data.get(str(chat_id), [])


def add_keyword(chat_id: int, keyword: str) -> list[str]:
    data = _load_data()
    cid = str(chat_id)
    keywords = data.get(cid, [])

    if keyword not in keywords:
        keywords.append(keyword)
        data[cid] = keywords
        _save_data(data)

    return keywords


def remove_keyword(chat_id: int, keyword: str) -> list[str]:
    data = _load_data()
    cid = str(chat_id)
    keywords = data.get(cid, [])

    if keyword in keywords:
        keywords.remove(keyword)
        data[cid] = keywords
        _save_data(data)

    return keywords
