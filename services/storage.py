
import os, json, uuid
from typing import Dict, Any, Optional

DB_PATH = os.environ.get("PUCH_DB_PATH", "doc_store.json")

def _load() -> Dict[str, Any]:
    if not os.path.exists(DB_PATH):
        return {"docs": {}}
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"docs": {}}

def _save(db: Dict[str, Any]) -> None:
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def create_doc(title: str, text: str) -> str:
    db = _load()
    doc_id = str(uuid.uuid4())
    db["docs"][doc_id] = {"title": title, "text": text, "meta": {}}
    _save(db)
    return doc_id

def get_doc(doc_id: str) -> Optional[Dict[str, Any]]:
    db = _load()
    return db["docs"].get(doc_id)

def set_meta(doc_id: str, key: str, value: Any) -> None:
    db = _load()
    if doc_id in db["docs"]:
        db["docs"][doc_id]["meta"][key] = value
        _save(db)

def list_docs():
    return _load()["docs"]
