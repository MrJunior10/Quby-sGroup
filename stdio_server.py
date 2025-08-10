
"""
Lightweight stdio server (JSON Lines). No external MCP dependency.

Protocol:
- Read lines from stdin, each must be a JSON object: {"tool": "<name>", "args": {...}}
- Write one JSON line as response: {"ok": true, "result": ...} or {"ok": false, "error": "..."}

Tools:
- ingest_text(title, text)
- ingest_url(url)
- summarize_doc(doc_id, target_words=150)
- chat_with_doc(doc_id, question)
- generate_flashcards(doc_id, num=10)
- translate_text(text, target_lang="hi")
- share_summary_link(doc_id, target_words=150)
- list_docs()
"""
import sys, os, json, string, random

from services.storage import create_doc, get_doc, set_meta, list_docs
from services.doc_parser import extract_from_url
from services.llm import summarize as llm_summarize, qa as llm_qa, flashcards as llm_flashcards, translate as llm_translate

def token(n=10):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))

def respond(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line: 
            continue
        try:
            req = json.loads(line)
            tool = req.get("tool")
            args = req.get("args", {})

            if tool == "ingest_text":
                title = args.get("title","Untitled")
                text = args.get("text","")
                doc_id = create_doc(title, text)
                respond({"ok": True, "result": {"doc_id": doc_id, "title": title}})

            elif tool == "ingest_url":
                url = args["url"]
                text = extract_from_url(url)
                doc_id = create_doc(url, text)
                respond({"ok": True, "result": {"doc_id": doc_id, "title": url}})

            elif tool == "summarize_doc":
                doc = get_doc(args["doc_id"])
                if not doc: raise ValueError("doc not found")
                target_words = int(args.get("target_words", 150))
                summary = llm_summarize(doc["text"], target_words)
                set_meta(args["doc_id"], "last_summary", summary)
                respond({"ok": True, "result": summary})

            elif tool == "chat_with_doc":
                doc = get_doc(args["doc_id"])
                if not doc: raise ValueError("doc not found")
                answer = llm_qa(doc["text"], args["question"])
                respond({"ok": True, "result": answer})

            elif tool == "generate_flashcards":
                doc = get_doc(args["doc_id"])
                if not doc: raise ValueError("doc not found")
                num = int(args.get("num", 10))
                cards = [{"q": q, "a": a} for (q,a) in llm_flashcards(doc["text"], num)]
                respond({"ok": True, "result": cards})

            elif tool == "translate_text":
                out = llm_translate(args["text"], args.get("target_lang","hi"))
                respond({"ok": True, "result": out})

            elif tool == "share_summary_link":
                doc = get_doc(args["doc_id"])
                if not doc: raise ValueError("doc not found")
                target_words = int(args.get("target_words", 150))
                summary = llm_summarize(doc["text"], target_words)
                os.makedirs("shares", exist_ok=True)
                t = token()
                path = os.path.join("shares", f"{t}.md")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(f"# Summary for: {doc.get('title','Untitled')}\n\n{summary}\n")
                set_meta(args["doc_id"], "share_token", t)
                respond({"ok": True, "result": {"token": t, "path": path}})

            elif tool == "list_docs":
                docs = list_docs()
                minimal = {k: {"title": v.get("title",""), "chars": len(v.get("text",""))} for k,v in docs.items()}
                respond({"ok": True, "result": minimal})

            else:
                respond({"ok": False, "error": f"Unknown tool: {tool}"})
        except Exception as e:
            respond({"ok": False, "error": str(e)})

if __name__ == "__main__":
    main()
