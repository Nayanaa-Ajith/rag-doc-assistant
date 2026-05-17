#!/usr/bin/env python3
"""
Standalone ingestion script — run once before starting the API.

Usage:
    python ingest.py                    # ingest all files in ./docs/
    python ingest.py --dir ./my_docs    # custom directory
    python ingest.py --url https://...  # ingest from URL
"""

import argparse
import os
import sys
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from app.vectorstore import ingest_file, ingest_text, list_documents


def ingest_url(url: str) -> int:
    print(f"Fetching {url}...")
    resp = requests.get(url, timeout=15, headers={"User-Agent": "RAG-Ingester/1.0"})
    resp.raise_for_status()

    if "html" in resp.headers.get("content-type", ""):
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
    else:
        text = resp.text

    doc_name = url.split("//")[-1].replace("/", "_")[:60]
    return ingest_text(text, doc_name)


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into ChromaDB")
    parser.add_argument("--dir", default="./docs", help="Directory of docs to ingest")
    parser.add_argument("--url", help="Single URL to ingest")
    parser.add_argument("--file", help="Single file to ingest")
    args = parser.parse_args()

    total_chunks = 0

    if args.url:
        chunks = ingest_url(args.url)
        total_chunks += chunks
        print(f"URL: {chunks} chunks")

    elif args.file:
        chunks = ingest_file(args.file)
        total_chunks += chunks

    else:
        doc_dir = Path(args.dir)
        if not doc_dir.exists():
            print(f"Directory '{doc_dir}' not found. Creating it...")
            doc_dir.mkdir(parents=True)
            print("Add .md, .txt, or .html files to docs/ and re-run.")
            return

        extensions = {".md", ".txt", ".html", ".htm", ".py", ".rst"}
        files = [f for f in doc_dir.rglob("*") if f.suffix.lower() in extensions]

        if not files:
            print(f"No supported files found in {doc_dir}/")
            return

        print(f"\nFound {len(files)} files to ingest:\n")
        for f in sorted(files):
            chunks = ingest_file(str(f), f.name)
            total_chunks += chunks

    print(f"\n{'='*50}")
    print(f"✓ Ingestion complete! Total chunks indexed: {total_chunks}")
    print(f"\nCurrently indexed documents:")
    for doc in list_documents():
        print(f"  • {doc['name']} ({doc['chunks']} chunks)")


if __name__ == "__main__":
    main()
