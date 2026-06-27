"""
Merge raw Kol-Zchut + Bituach Leumi pages into a chunked passage corpus.

Output: data/processed/corpus.jsonl, one passage per line:
  {
    "chunk_id":  "kolzchut_12345_3",   # stable: <doc_id>_<chunk index>
    "doc_id":    "kolzchut_12345",     # page-level id (ground-truth granularity)
    "title":     "דמי אבטלה",
    "url":       "https://...",
    "source":    "kolzchut" | "btl",
    "domain":    "unemployment",
    "text":      "<clean passage for display / semantic encoding>",
    "text_norm": "<normalized token stream for lexical models>"
  }

`doc_id` is what evaluation scores against: a query is "hit" when a retrieved
chunk belongs to a ground-truth document.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
import preprocess  # noqa: E402
import scrape_btl  # noqa: E402
import scrape_kolzchut  # noqa: E402


def _doc_id(rec):
    return f"{rec['source']}_{rec['page_id']}"


def build(force_scrape=False):
    pages = scrape_kolzchut.scrape(force=force_scrape) + scrape_btl.scrape(force=force_scrape)
    print(f"[corpus] {len(pages)} source pages")

    rows, n_chunks = [], 0
    for rec in pages:
        doc_id = _doc_id(rec)
        clean = preprocess.clean_passage(rec["text"])
        chunks = preprocess.chunk_document(clean)
        for idx, ch in enumerate(chunks):
            rows.append(
                {
                    "chunk_id": f"{doc_id}_{idx}",
                    "doc_id": doc_id,
                    "title": rec["title"],
                    "url": rec["url"],
                    "source": rec["source"],
                    "domain": rec["domain"],
                    "text": ch,
                    "text_norm": preprocess.normalize_for_index(f"{rec['title']} {ch}"),
                }
            )
        n_chunks += len(chunks)

    with open(config.CORPUS_PATH, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    n_docs = len({r["doc_id"] for r in rows})
    by_source = {}
    for r in rows:
        by_source[r["source"]] = by_source.get(r["source"], 0) + 1
    print(f"[corpus] {n_docs} docs -> {len(rows)} chunks ({by_source}) -> {config.CORPUS_PATH}")
    return rows


def load_corpus(path=None):
    path = path or config.CORPUS_PATH
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


if __name__ == "__main__":
    build(force_scrape="--force" in sys.argv)
