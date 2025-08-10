import os, io, re, tempfile
from typing import Tuple
from pdfminer.high_level import extract_text as pdf_extract_text
import docx2txt
import magic  # Make sure you installed python-magic-bin

def clean_text(s: str) -> str:
    s = s.replace("\r", " ").replace("\t", " ")
    s = re.sub(r"[ \xa0]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def from_pdf_bytes(data: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(data)
        tmp.flush()
        path = tmp.name
    try:
        text = pdf_extract_text(path) or ""
    finally:
        try: os.remove(path)
        except Exception: pass
    return clean_text(text)

def from_docx_bytes(data: bytes) -> str:
    with tempfile.TemporaryDirectory() as td:
        fpath = os.path.join(td, "doc.docx")
        with open(fpath, "wb") as f:
            f.write(data)
        text = docx2txt.process(fpath) or ""
    return clean_text(text)

def from_txt_bytes(data: bytes) -> str:
    for encoding in ["utf-8", "utf-16", "latin-1"]:
        try:
            return clean_text(data.decode(encoding, errors="ignore"))
        except Exception:
            continue
    return ""

def sniff_and_extract(filename: str, data: bytes) -> Tuple[str, str]:
    name = os.path.basename(filename)
    title = os.path.splitext(name)[0] or "Untitled"
    ext = os.path.splitext(name)[1].lower()

    try:
        mime = magic.from_buffer(data, mime=True)
    except Exception:
        mime = ""

    if mime == "application/pdf" or ext == ".pdf":
        return title, from_pdf_bytes(data)
    elif mime in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword"
    ] or ext == ".docx":
        return title, from_docx_bytes(data)
    elif mime.startswith("text/") or ext in [".txt", ".md", ".rtf"]:
        return title, from_txt_bytes(data)
    else:
        # fallback
        try:
            text = from_pdf_bytes(data)
            if len(text.strip()) > 20:
                return title, text
        except:
            pass
        return title, from_txt_bytes(data)
