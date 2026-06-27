"""
Qualitative error analysis: where do the retrievers disagree, and why?

Produces results/error_analysis.md with >= 10 worked examples grouped into:
  A. Semantic wins / lexical fails  — synonymy & colloquial-vs-formal phrasing.
  B. Lexical wins / semantic fails  — exact-term / rare-token queries.
  C. Both fail                       — hard cases (out-of-vocab, ambiguous, sparse).

For each example we show the query, the ground-truth title(s), and each model's
top-3 documents, plus a short automatic diagnosis based on the phrasing_gap tag
and lexical overlap between query and the gold title.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
import evaluate  # noqa: E402
import preprocess  # noqa: E402


def _doc_titles(corpus):
    m = {}
    for r in corpus:
        m.setdefault(r["doc_id"], r["title"])
    return m


def _ranking(retriever, query, k=3):
    seen, out = set(), []
    for h in retriever.search(query, 20):
        if h["doc_id"] not in seen:
            seen.add(h["doc_id"])
            out.append(h)
        if len(out) == k:
            break
    return out


def _rank_of(retriever, query, relevant, topn=10):
    seen, rank = set(), 0
    for h in retriever.search(query, topn * 3):
        if h["doc_id"] in seen:
            continue
        seen.add(h["doc_id"])
        rank += 1
        if h["doc_id"] in relevant:
            return rank
    return None


def _lexical_overlap(query, title):
    stop = set(preprocess.HEB_STOPWORDS)
    q = {t for t in preprocess.normalize_for_index(query).split() if t not in stop}
    t = {w for w in preprocess.normalize_for_index(title).split() if w not in stop}
    return len(q & t)


def build(retrievers_dict, corpus, queries=None, lexical="tfidf", semantic="semantic"):
    queries = queries or evaluate.load_eval()
    titles = _doc_titles(corpus)
    lex, sem = retrievers_dict[lexical], retrievers_dict[semantic]

    cats = {"A_semantic_wins": [], "B_lexical_wins": [], "C_both_fail": []}
    for q in queries:
        relevant = set(q["relevant_doc_ids"])
        lr = _rank_of(lex, q["query"], relevant)
        sr = _rank_of(sem, q["query"], relevant)
        lhit = lr is not None and lr <= 3
        shit = sr is not None and sr <= 3
        rec = {"q": q, "lr": lr, "sr": sr}
        if shit and not lhit:
            cats["A_semantic_wins"].append(rec)
        elif lhit and not shit:
            cats["B_lexical_wins"].append(rec)
        elif not lhit and not shit:
            cats["C_both_fail"].append(rec)

    lines = ["# Error Analysis — Lexical (TF-IDF) vs. Semantic (AlephBERT)\n"]
    lines.append(
        "Each query is judged at document level (top-3). Rank `None` means the "
        "gold document was not retrieved in the top results. The diagnosis combines "
        "the manual `phrasing_gap` tag with the literal word overlap between the "
        "query and the gold title.\n"
    )

    headers = {
        "A_semantic_wins": "## A. Semantic wins, lexical fails (synonymy / colloquial → formal)",
        "B_lexical_wins": "## B. Lexical wins, semantic fails (exact-term advantage)",
        "C_both_fail": "## C. Both fail (hard cases)",
    }
    n = 0
    for cat, recs in cats.items():
        lines.append("\n" + headers[cat] + "\n")
        if not recs:
            lines.append("_No cases in this category._\n")
        for rec in recs:
            n += 1
            q = rec["q"]
            gold = [titles.get(d, d) for d in q["relevant_doc_ids"]]
            overlap = max((_lexical_overlap(q["query"], t) for t in gold), default=0)
            lines.append(f"**{n}. [{q['id']} · {q['domain']}] “{q['query']}”**  ")
            lines.append(f"- Gold: {', '.join(gold)}  ")
            lines.append(
                f"- Lexical top-3: {', '.join(titles.get(h['doc_id'], h['doc_id']) for h in _ranking(lex, q['query']))}  "
            )
            lines.append(
                f"- Semantic top-3: {', '.join(titles.get(h['doc_id'], h['doc_id']) for h in _ranking(sem, q['query']))}  "
            )
            lines.append(
                f"- Gold rank — lexical: {rec['lr']}, semantic: {rec['sr']}  "
            )
            lines.append(
                f"- Diagnosis: phrasing_gap=`{q['phrasing_gap']}`, query↔gold-title word overlap=`{overlap}`. "
                + _diagnose(cat, q, overlap)
                + "\n"
            )

    lines.insert(
        2,
        f"\n**Summary:** {len(cats['A_semantic_wins'])} semantic-wins, "
        f"{len(cats['B_lexical_wins'])} lexical-wins, "
        f"{len(cats['C_both_fail'])} both-fail "
        f"(out of {len(queries)} queries).\n",
    )

    with open(config.ERROR_ANALYSIS_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[error-analysis] {n} examples -> {config.ERROR_ANALYSIS_PATH}")
    return cats


def _diagnose(cat, q, overlap):
    if cat == "A_semantic_wins":
        if overlap == 0:
            return "Zero shared content words — lexical had nothing to match; embeddings bridged the vocabulary gap."
        return "Low surface overlap; the embedding captured meaning the sparse model under-weighted."
    if cat == "B_lexical_wins":
        return "Distinctive shared term(s) gave the sparse model a precise signal the embedding diffused."
    return "Sparse corpus coverage / ambiguous phrasing — neither signal was strong enough."


if __name__ == "__main__":
    import build_corpus
    import retrievers as R

    corpus = build_corpus.load_corpus()
    build(R.build_all(corpus), corpus)
