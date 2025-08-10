from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel

import os, string, random, json

from services.storage import create_doc, get_doc, set_meta, list_docs
from services.doc_parser import extract_from_url
from services.file_ingest import sniff_and_extract
from services.llm import summarize as llm_summarize, qa as llm_qa, flashcards as llm_flashcards, translate as llm_translate

app = FastAPI(title="Puch Doc Chat - HTTP API")

class IngestText(BaseModel):
    title: str
    text: str

class IngestURL(BaseModel):
    url: str

class SummarizeReq(BaseModel):
    doc_id: str
    target_words: int = 150

class ChatReq(BaseModel):
    doc_id: str
    question: str

class FlashReq(BaseModel):
    doc_id: str
    num: int = 10

class TranslateReq(BaseModel):
    text: str
    target_lang: str = "hi"

class TranslateDocReq(BaseModel):
    doc_id: str
    target_lang: str = "hi"

class ShareReq(BaseModel):
    doc_id: str
    target_words: int = 150

def token(n=10):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))

@app.post("/ingest_text")
def ingest_text(payload: IngestText):
    doc_id = create_doc(payload.title, payload.text)
    return {"doc_id": doc_id, "title": payload.title}

@app.post("/ingest_file")
async def ingest_file(file: UploadFile = File(...), title: str | None = Form(None)):
    data = await file.read()
    inferred_title, text = sniff_and_extract(file.filename, data)
    use_title = title or inferred_title
    doc_id = create_doc(use_title, text)
    return {"doc_id": doc_id, "title": use_title, "chars": len(text)}

@app.post("/ingest_url")
def ingest_url(payload: IngestURL):
    text = extract_from_url(payload.url)
    doc_id = create_doc(payload.url, text)
    return {"doc_id": doc_id, "title": payload.url}

@app.post("/summarize_doc")
def summarize_doc(payload: SummarizeReq):
    doc = get_doc(payload.doc_id)
    if not doc:
        return {"error": "doc not found"}

    print(f"Summarizing doc {payload.doc_id} with target_words={payload.target_words}")
    s = llm_summarize(doc["text"], payload.target_words)
    set_meta(payload.doc_id, "last_summary", s)
    return {"summary": s}

@app.post("/chat_with_doc")
def chat_with_doc(payload: ChatReq):
    doc = get_doc(payload.doc_id)
    if not doc:
        return {"error": "doc not found"}
    ans = llm_qa(doc["text"], payload.question)
    return {"answer": ans}

@app.post("/generate_flashcards")
def generate_flashcards(payload: FlashReq):
    doc = get_doc(payload.doc_id)
    if not doc:
        return {"error": "doc not found"}
    cards = [{"q": q, "a": a} for (q, a) in llm_flashcards(doc["text"], payload.num)]
    return {"cards": cards}

@app.post("/translate_text")
def translate_text(payload: TranslateReq):
    out = llm_translate(payload.text, payload.target_lang)
    return {"translation": out}

@app.post("/translate_doc")
def translate_doc(payload: TranslateDocReq):
    doc = get_doc(payload.doc_id)
    if not doc:
        return {"error": "doc not found"}
    out = llm_translate(doc["text"], payload.target_lang)
    return {"translation": out}

@app.post("/share_summary_link")
def share_summary_link(payload: ShareReq):
    doc = get_doc(payload.doc_id)
    if not doc:
        return {"error": "doc not found"}
    s = llm_summarize(doc["text"], payload.target_words)
    os.makedirs("shares", exist_ok=True)
    t = token()
    path = os.path.join("shares", f"{t}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Summary for: {doc.get('title', 'Untitled')}\n\n{s}\n")
    set_meta(payload.doc_id, "share_token", t)
    return {"token": t, "path": path}

@app.get("/list_docs")
def list_docs_endpoint():
    docs = list_docs()
    minimal = {k: {"title": v.get("title", ""), "chars": len(v.get("text", ""))} for k, v in docs.items()}
    return minimal

@app.get("/mcp")
def validate():
    return {"validate": "919475046489"}  # Replace with your own phone number in +91 format
