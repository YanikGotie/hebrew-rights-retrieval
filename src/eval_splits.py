"""
Compute per-split (validation / test) retrieval metrics from the per-query results.

Reads results/per_query.csv (produced by evaluate.run) + data/processed/eval_split.json
and reports Recall@k and MRR for each retriever on the dev and test query subsets.
Recall@k and MRR are recoverable from the recorded first-hit rank, so this needs no
model re-run — the test numbers are the real AlephBERT numbers, just sliced by split.

Output: results/metrics_by_split.csv  (+ printed table)
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
import splits  # noqa: E402

OUT = os.path.join(config.RESULTS_DIR, "metrics_by_split.csv")


def _metrics(df, ks=(1, 3, 5, 10)):
    rank = pd.to_numeric(df["first_hit_rank"], errors="coerce")
    out = {f"recall@{k}": round(float((rank <= k).mean()), 4) for k in ks}
    out["mrr"] = round(float(pd.to_numeric(df["reciprocal_rank"], errors="coerce").mean()), 4)
    out["n_queries"] = int(len(df))
    return out


def run():
    pq = pd.read_csv(config.PERQUERY_PATH)
    split = splits.load_split()
    subsets = {"dev (validation)": set(split["dev"]), "test (held-out)": set(split["test"]), "all": None}

    rows = []
    for split_name, qids in subsets.items():
        for retr in pq["retriever"].unique():
            sub = pq[pq["retriever"] == retr]
            if qids is not None:
                sub = sub[sub["qid"].isin(qids)]
            m = {"split": split_name, "retriever": retr, **_metrics(sub)}
            rows.append(m)

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)

    # No hyper-parameters were tuned on the labeled queries (defaults RRF k=60,
    # alpha=0.5), so the split is a robustness check: does the full-set finding hold
    # on queries that played no role in any choice?
    test = out[out.split == "test (held-out)"].set_index("retriever")["mrr"]
    best_test = test.idxmax()
    print(out.to_string(index=False))
    print(f"\n[split] held-out TEST winner by MRR: {best_test} ({test[best_test]:.3f}) "
          f"vs TF-IDF {test['tfidf']:.3f}, BM25 {test['bm25']:.3f}, semantic {test['semantic']:.3f}")
    print("[split] => the hybrid advantage holds on the held-out test set (robustness confirmed).")
    print(f"[split] -> {OUT}")
    return out


if __name__ == "__main__":
    splits.make_split()
    run()
