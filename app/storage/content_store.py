# app/storage/content_store.py
import os
import hashlib

STORAGE_DIR = "./data"


def _ensure_dir():
    os.makedirs(STORAGE_DIR, exist_ok=True)


def save_content(content: str) -> str:
    """存正文，返回 key（内容哈希）。已存在则不重写。"""
    key = hashlib.md5(content.encode("utf-8")).hexdigest()
    _ensure_dir()
    path = os.path.join(STORAGE_DIR, f"{key}.txt")
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    return key


def load_content(key: str) -> str:
    """按 key 取正文。key 不存在 → FileNotFoundError。"""
    path = os.path.join(STORAGE_DIR, f"{key}.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()