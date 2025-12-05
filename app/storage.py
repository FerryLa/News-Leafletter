# storage.py
import json
from pathlib import Path

# 이 파일(app/storage.py) 기준으로 프로젝트 루트 / data / watchlist.json 위치 잡기
BASE_DIR = Path(__file__).resolve().parents[1]  # News-Leafletter/
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "watchlist.json"


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
    # data 폴더 없으면 여기서라도 만들어주기
    DATA_DIR.mkdir(parents=True, exist_ok=True)
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
