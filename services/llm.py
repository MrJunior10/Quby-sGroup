import os, re
from typing import List, Tuple
from collections import Counter

def _has_key() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))

def _split_into_sentences(text: str) -> List[str]:
    parts = re.split(r'(?<=[\.!?])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]

def heuristic_summary(text: str, target_words: int = 150) -> str:
    sentences = _split_into_sentences(text)
    if not sentences:
        return ""
    out, count = [], 0
    for s in sentences:
        w = s.split()
        if count + len(w) > target_words and out:
            break
        out.append(s)
        count += len(w)
    if not out:
        out = sentences[:3]
    return " ".join(out)

def keyword_chunks(text: str, chunk_size: int = 1000, overlap: int = 150) -> List[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i+chunk_size]
        chunks.append(" ".join(chunk))
        i += max(1, chunk_size - overlap)
    return chunks

def simple_retrieve(chunks: List[str], question: str, top_k: int = 3) -> List[str]:
    q_terms = set([t.lower() for t in re.findall(r"\w+", question)])
    scored = []
    for ch in chunks:
        tokens = [t.lower() for t in re.findall(r"\w+", ch)]
        cnt = Counter(tokens)
        score = sum(cnt[t] for t in q_terms)
        scored.append((score, ch))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for s, c in scored[:top_k] if s > 0] or [chunks[0]]

# 🧠 Use OpenRouter-compatible client
def get_openai_client():
    from openai import OpenAI
    return OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
    )

def openai_summary(text: str, target_words: int = 150) -> str:
    client = get_openai_client()
    print("🔵 Using OpenAI GPT summarizer...")
    prompt = f"Summarize the following text in about {target_words} words, using crisp bullets if helpful:\n\n{text}"
    resp = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()

def openai_answer(context: str, question: str) -> str:
    client = get_openai_client()
    print("🔵 Using OpenAI GPT for QA...")
    prompt = f"Use ONLY the provided context to answer.\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
    resp = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()

def summarize(text: str, target_words: int = 150) -> str:
    if _has_key():
        try:
            return openai_summary(text, target_words)
        except Exception as e:
            print(f"🔴 OpenAI summarization failed: {e}")
    print("⚪ Using fallback heuristic summarizer.")
    return heuristic_summary(text, target_words)

def qa(text: str, question: str) -> str:
    chunks = keyword_chunks(text)
    ctxs = simple_retrieve(chunks, question)
    context = "\n\n---\n\n".join(ctxs)
    if _has_key():
        try:
            return openai_answer(context, question)
        except Exception as e:
            print(f"🔴 OpenAI QA failed: {e}")
    print("⚪ Using fallback QA.")
    return f"(Heuristic answer)\nTop context:\n{context[:1200]}\n\nQ: {question}\n"

def flashcards(text: str, num: int = 10) -> List[Tuple[str, str]]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    cards, i = [], 0
    for ln in lines:
        if len(cards) >= num:
            break
        if len(ln.split()) >= 3 and ln.endswith((".", ":", "—", "-")):
            cards.append((f"What does this refer to: '{ln[:80]}'?", ln))
    while len(cards) < num and i < len(lines):
        ln = lines[i]
        cards.append((f"Key point {len(cards)+1}?", ln))
        i += 1
    return cards

def translate(text: str, target_lang: str = "hi") -> str:
    if _has_key():
        try:
            client = get_openai_client()
            print(f"🔵 Using OpenAI for translation to '{target_lang}'...")
            prompt = f"Translate to {target_lang}:\n\n{text}"
            resp = client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"🔴 Translation failed: {e}")
    print(f"⚪ Fallback: translation to {target_lang} unavailable.")
    return f"[{target_lang} translation unavailable offline]\n{text}"
