"""
Evaluate retrievers on the hand-authored eval set with standard IR metrics.

Metrics (document-level; a chunk counts for its parent doc_id):
  * Recall@k   — fraction of queries with >=1 relevant doc in the top-k.
  * MRR        — mean reciprocal rank of the first relevant doc.
  * nDCG@k     — normalized discounted cumulative gain (graded by position).
  * MAP        — mean average precision over the returned ranking.

Outputs:
  results/metrics.csv     — one row per retriever, all metrics.
  results/per_query.csv   — per-(retriever,query) first-hit rank + reciprocal rank.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402


def load_eval(path=None):
    path = path or config.EVAL_PATH
    return json.load(open(path, encoding="utf-8"))["queries"]


def _ranked_doc_ids(hits):
    """Collapse chunk hits to a de-duplicated document ranking (best chunk wins)."""
    seen, docs = set(), []
    for h in hits:
        if h["doc_id"] not in seen:
            seen.add(h["doc_id"])
            docs.append(h["doc_id"])
    return docs


def _first_hit_rank(doc_ranking, relevant):
    for i, d in enumerate(doc_ranking, 1):
        if d in relevant:
            return i
    return None


def _ndcg(doc_ranking, relevant, k):
    dcg = 0.0
    for i, d in enumerate(doc_ranking[:k], 1):
        if d in relevant:
            dcg += 1.0 / np.log2(i + 1)
    ideal = sum(1.0 / np.log2(i + 1) for i in range(1, min(len(relevant), k) + 1))
    return dcg / ideal if ideal > 0 else 0.0


def _average_precision(doc_ranking, relevant):
    hits, score = 0, 0.0
    for i, d in enumerate(doc_ranking, 1):
        if d in relevant:
            hits += 1
            score += hits / i
    return score / len(relevant) if relevant else 0.0


def evaluate_retriever(retriever, queries, k_values=None, topn=None):
    k_values = k_values or config.K_VALUES
    topn = topn or max(k_values)
    per_query = []
    agg = {f"recall@{k}": [] for k in k_values}
    agg.update({"mrr": [], f"ndcg@{max(k_values)}": [], "map": []})

    for q in queries:
        relevant = set(q["relevant_doc_ids"])
        hits = retriever.search(q["query"], topn)
        ranking = _ranked_doc_ids(hits)
        first = _first_hit_rank(ranking, relevant)
        rr = 1.0 / first if first else 0.0

        for k in k_values:
            agg[f"recall@{k}"].append(1.0 if first and first <= k else 0.0)
        agg["mrr"].append(rr)
        agg[f"ndcg@{max(k_values)}"].append(_ndcg(ranking, relevant, max(k_values)))
        agg["map"].append(_average_precision(ranking, relevant))

        per_query.append(
            {
                "retriever": retriever.name,
                "qid": q["id"],
                "domain": q["domain"],
                "phrasing_gap": q["phrasing_gap"],
                "query": q["query"],
                "first_hit_rank": first if first else "",
                "reciprocal_rank": round(rr, 4),
                "top1_doc": ranking[0] if ranking else "",
            }
        )

    metrics = {"retriever": retriever.name}
    metrics.update({m: round(float(np.mean(v)), 4) for m, v in agg.items()})
    return metrics, per_query


def run(retrievers_dict, queries=None):
    queries = queries or load_eval()
    rows, per_query_all = [], []
    for name, r in retrievers_dict.items():
        m, pq = evaluate_retriever(r, queries)
        rows.append(m)
        per_query_all.extend(pq)
        print(f"[eval] {name:16s} " + "  ".join(f"{k}={v}" for k, v in m.items() if k != "retriever"))

    metrics_df = pd.DataFrame(rows).set_index("retriever")
    metrics_df.to_csv(config.METRICS_PATH)
    pd.DataFrame(per_query_all).to_csv(config.PERQUERY_PATH, index=False)
    print(f"\n[eval] metrics -> {config.METRICS_PATH}")
    print(f"[eval] per-query -> {config.PERQUERY_PATH}")
    return metrics_df, pd.DataFrame(per_query_all)


if __name__ == "__main__":
    import build_corpus
    import retrievers as R

    corpus = build_corpus.load_corpus()
    run(R.build_all(corpus))
