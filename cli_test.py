# cli_test.py
import uuid
import argparse
from pathlib import Path

from library.manager import DocumentManager
from embed.vectorizer import VectorStore
from rag.pipeline import RAGPipeline
import config

parser = argparse.ArgumentParser()
parser.add_argument("mode", choices=["add", "chat", "list"])
parser.add_argument("file", nargs="?")
args = parser.parse_args()

dm = DocumentManager(config.LIBRARY_META_PATH)
vs = VectorStore(model_name=config.EMBED_MODEL_NAME, index_path=config.INDEX_PATH, meta_path=config.META_PATH)
rag = RAGPipeline(vs)

if args.mode == "list":
    docs = dm.list_documents()
    if not docs:
        print("[RAG] No documents.")
    else:
        for d in docs:
            print(f"{d['doc_id']}\n  File:  {d['name']}\n  Pages: {d.get('pages','?')}\n  Chunks:{d.get('chunks',0)}\n")
    exit()

if args.mode == "add":
    if not args.file:
        print("Provide a file path.")
        exit()
    fp = Path(args.file)
    if not fp.exists():
        print("File not found.")
        exit()
    doc_id = str(uuid.uuid4())
    print(f"[+] Ingesting: {fp.name}")
    chunks = dm.ingest_document(str(fp), doc_id)
    # persist chunks to vectorstore
    stored = vs.add_with_return(chunks, doc_id, fp.name, dm.db.get_all()[-1].get("pages", 1))
    vs.save()
    print(f"[+] Ingested {len(stored)} chunks for {fp.name}")
    exit()

if args.mode == "chat":
    print("[Chat Mode] Type 'exit' to quit.")
    while True:
        try:
            q = input(">> ").strip()
            if not q:
                continue
            if q.lower() in ("exit", "quit"):
                print("Exiting...")
                break
            ans = rag.query(q)
            print("\n--- Answer ---\n" + ans + "\n")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
