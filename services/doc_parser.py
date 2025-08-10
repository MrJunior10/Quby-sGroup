
import re, requests
from bs4 import BeautifulSoup

def clean_text(s: str) -> str:
    s = s.replace("\r", " ").replace("\t", " ")
    s = re.sub(r"[ \xa0]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

CANDIDATE_SELECTORS = [
    "article",
    "main",
    "[role='main']",
    ".article",
    ".post",
    ".entry-content",
    ".content",
]

def extract_from_url(url: str) -> str:
    """Lightweight, pure-Python main-text extractor (no lxml).
    Heuristics: pick the largest text block from likely containers,
    fallback to document-wide paragraphs.
    """
    resp = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html5lib")

    # Remove obviously noisy nodes
    for tag in soup(["script","style","nav","footer","header","noscript","iframe","aside","form","input","button","svg"]):
        tag.decompose()

    # Try candidate containers
    best_text = ""
    for sel in CANDIDATE_SELECTORS:
        for node in soup.select(sel):
            # collect text from paragraphs and headers inside node
            parts = []
            for p in node.find_all(["p","h1","h2","h3","li"]):
                t = p.get_text(" ", strip=True)
                if t and len(t.split()) >= 3:
                    parts.append(t)
            text = "\n".join(parts)
            if len(text) > len(best_text):
                best_text = text

    # Fallback: all paragraphs in body
    if len(best_text) < 300:
        parts = []
        for p in soup.body.find_all(["p","li","h1","h2","h3"]) if soup.body else []:
            t = p.get_text(" ", strip=True)
            if t and len(t.split()) >= 3:
                parts.append(t)
        best_text = "\n".join(parts) if parts else soup.get_text("\n", strip=True)

    return clean_text(best_text)
