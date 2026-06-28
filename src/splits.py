"""
Evaluation protocol — the train / validation / test split.

This is an *information-retrieval* project, so the split is query-level, not the
usual supervised row-level split:

  * "Train" / index-fitting data = the **corpus** (`corpus.jsonl`). The lexical
    models fit their vocabulary + IDF statistics on it and the semantic model
    encodes it. No ground-truth labels are used here.
  * Labeled data = the 40 query→relevant-document pairs (`eval_set.json`).
    These are split, stratified by domain with a fixed seed, into:
       - **validation / dev** (~35%): used for *model selection* and any
         hyper-parameter choice (e.g. RRF vs. weighted fusion, fusion weight α).
       - **test** (~65%): held out; reported as the final, unbiased numbers.

Splitting at the query level is what prevents leakage: hyper-parameters are
chosen on dev queries the test queries never influence.

Run: python src/splits.py   ->  writes data/processed/eval_split.json
"""
from __future__ import annotations

import json
import os
import random
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402

SPLIT_PATH = os.path.join(config.PROCESSED_DIR, "eval_split.json")
DEV_FRACTION = 0.35


def make_split(dev_fraction=DEV_FRACTION, seed=config.RANDOM_SEED):
    queries = json.load(open(config.EVAL_PATH, encoding="utf-8"))["queries"]
    by_domain = defaultdict(list)
    for q in queries:
        by_domain[q["domain"]].append(q["id"])

    rng = random.Random(seed)
    dev, test = [], []
    for domain in sorted(by_domain):
        qids = sorted(by_domain[domain])
        rng.shuffle(qids)
        n_dev = max(1, round(len(qids) * dev_fraction)) if len(qids) > 1 else 0
        dev.extend(qids[:n_dev])
        test.extend(qids[n_dev:])

    split = {
        "seed": seed,
        "dev_fraction": dev_fraction,
        "dev": sorted(dev),
        "test": sorted(test),
        "note": "Query-level split, stratified by domain. Corpus = index (no labels). "
                "dev = model selection / hyper-parameters; test = held-out final metrics.",
    }
    with open(SPLIT_PATH, "w", encoding="utf-8") as f:
        json.dump(split, f, ensure_ascii=False, indent=2)
    print(f"[split] dev={len(dev)} test={len(test)} -> {SPLIT_PATH}")
    return split


def load_split():
    if not os.path.exists(SPLIT_PATH):
        return make_split()
    return json.load(open(SPLIT_PATH, encoding="utf-8"))


if __name__ == "__main__":
    s = make_split()
    print("dev :", s["dev"])
    print("test:", s["test"])
