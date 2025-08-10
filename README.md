
# Puch Doc Chat — Migrated Template (No private MCP deps)

This repo gives you **two ways to run** right now without any private SDKs:

1) **`stdio_server.py`** — a tiny JSON-lines stdio protocol
   - Accepts: one JSON object per line on stdin
   - Returns: one JSON object per line on stdout
   - Ideal until you plug into the official Puch MCP SDK.

2) **`http_server.py`** — a FastAPI HTTP server
   - Easy to test locally or deploy on Render.
   - Endpoints mirror your tools.

## Install

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Make sure the right readability package:
pip uninstall -y readability
pip install readability-lxml
```

(Optional) LLM quality boost:
```bash
export OPENAI_API_KEY=sk-...   # Windows PowerShell: $Env:OPENAI_API_KEY="sk-..."
```

## Run — STDIO mode

```bash
python stdio_server.py
```
In another shell, you can send JSON lines:
```bash
# example on Unix; on Windows, use PowerShell equivalents
printf '{"tool":"ingest_text","args":{"title":"Demo","text":"Hello world. This is a long text."}}\n' | python stdio_server.py
```

## Run — HTTP mode

```bash
uvicorn http_server:app --host 0.0.0.0 --port 8000
```

Test:
```
POST /ingest_text       {"title":"Demo","text":"..."}  -> {"doc_id": "..."}
POST /summarize_doc     {"doc_id":"...","target_words":150}
POST /chat_with_doc     {"doc_id":"...","question":"What is ...?"}
POST /generate_flashcards{"doc_id":"...","num":8}
POST /translate_text    {"text":"Hello","target_lang":"hi"}
POST /share_summary_link{"doc_id":"..."}
GET  /list_docs
```

## When you get the official Puch MCP SDK

- Replace this stdio loop with their `server.run_stdio()` glue.
- Your service code in `services/` already stays the same.
- Map each endpoint/tool to an MCP tool definition.

Good luck on the leaderboard!


### File Uploads (PDF / DOCX / TXT)

```bash
uvicorn http_server:app --host 0.0.0.0 --port 8000
```

**POST /ingest_file** (multipart/form-data):
- `file`: your document (pdf/docx/txt)
- `title` (optional): override title

Response:
```json
{ "doc_id": "...", "title": "Your Title", "chars": 12345 }
```

Then call:
- `POST /summarize_doc` → `{"doc_id":"...","target_words":150}`
- `POST /chat_with_doc` → `{"doc_id":"...","question":"..."}`
- `POST /generate_flashcards` → `{"doc_id":"...","num":10}`
- `POST /share_summary_link` → `{"doc_id":"..."}`
```
