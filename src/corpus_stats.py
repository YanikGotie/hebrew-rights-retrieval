"""
Descriptive NLP statistics for the corpus — the "raw" classical-NLP view.

Reports, with concrete numbers:
  * corpus size (docs / chunks / tokens), per-domain and per-source breakdown,
  * a worked tokenization example (raw -> niqqud-stripped -> tokens -> stopwords removed),
  * TF-IDF vectorizer internals: vocabulary size, matrix shape, sparsity, unigram/bigram
    split, top global terms by document frequency, and a single passage shown as its
    sparse TF-IDF vector (the top weighted terms),
  * a light prefix-stripping ("poor-man's lemmatization") experiment and its effect on
    vocabulary size — illustrating why Hebrew morphology inflates the lexical space.

Run: python src/corpus_stats.py   (writes results/corpus_stats.json, prints a summary)
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build_corpus  # noqa: E402
import config  # noqa: E402
import preprocess  # noqa: E402

# Hebrew attached particles often glued to the front of a word.
_PREFIXES = ("ושה", "כשה", "לכש", "מה", "שה", "וש", "כש", "לכ", "ב", "ל", "מ", "ה", "ו", "ש", "כ")


def light_stem(token: str) -> str:
    """Strip one leading particle if a reasonable stem remains (concept demo only)."""
    for p in sorted(_PREFIXES, key=len, reverse=True):
        if token.startswith(p) and len(token) - len(p) >= 3:
            return token[len(p):]
    return token


def main():
    corpus = build_corpus.load_corpus()
    stop = set(preprocess.HEB_STOPWORDS)

    # ---- size ---------------------------------------------------------------
    docs = {r["doc_id"] for r in corpus}
    by_domain = Counter(r["domain"] for r in corpus)
    by_source = Counter(r["source"] for r in corpus)
    tok_lists = [r["text_norm"].split() for r in corpus]
    tok_counts = [len(t) for t in tok_lists]
    total_tokens = sum(tok_counts)
    vocab_raw = {t for toks in tok_lists for t in toks}

    # ---- worked tokenization example ---------------------------------------
    sample = next(r for r in corpus if r["title"] == "דמי אבטלה" and r["source"] == "kolzchut")
    raw = sample["text"][:180]
    norm = preprocess.normalize_for_index(raw)
    toks = norm.split()
    toks_nostop = [t for t in toks if t not in stop]

    # ---- TF-IDF internals ---------------------------------------------------
    from sklearn.feature_extraction.text import TfidfVectorizer

    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, token_pattern=r"(?u)\b\w+\b",
                          stop_words=preprocess.HEB_STOPWORDS, sublinear_tf=True)
    X = vec.fit_transform([r["text_norm"] for r in corpus])
    vocab = vec.get_feature_names_out()
    n_uni = sum(1 for w in vocab if " " not in w)
    n_bi = len(vocab) - n_uni
    sparsity = 1.0 - X.nnz / (X.shape[0] * X.shape[1])

    # top global terms by document frequency
    df = np.asarray((X > 0).sum(axis=0)).ravel()
    top_df = sorted(zip(vocab, df), key=lambda kv: -kv[1])[:15]

    # one passage as a sparse TF-IDF vector (top weighted terms) — use the same
    # passage shown in the tokenization example above.
    sample_idx = next(i for i, r in enumerate(corpus) if r["chunk_id"] == sample["chunk_id"])
    row = X[sample_idx].tocoo()
    top_terms = sorted(zip(row.col, row.data), key=lambda kv: -kv[1])[:10]
    passage_vector = [(vocab[c], round(float(w), 3)) for c, w in top_terms]

    # ---- light stemming effect ---------------------------------------------
    vocab_stem = {light_stem(t) for t in vocab_raw}

    stats = {
        "n_docs": len(docs),
        "n_chunks": len(corpus),
        "by_source": dict(by_source),
        "by_domain": dict(by_domain),
        "total_tokens_after_norm": total_tokens,
        "avg_tokens_per_chunk": round(total_tokens / len(corpus), 1),
        "median_tokens_per_chunk": int(np.median(tok_counts)),
        "raw_vocabulary_types": len(vocab_raw),
        "stopwords_count": len(stop),
        "tokenization_example": {
            "raw_snippet": raw,
            "normalized": norm,
            "n_tokens": len(toks),
            "n_tokens_after_stopwords": len(toks_nostop),
            "removed_stopwords": [t for t in toks if t in stop][:12],
            "tokens_after_stopwords": toks_nostop[:18],
        },
        "tfidf": {
            "matrix_shape": list(X.shape),
            "vocabulary_size": len(vocab),
            "n_unigrams": n_uni,
            "n_bigrams": n_bi,
            "nnz": int(X.nnz),
            "sparsity_pct": round(sparsity * 100, 3),
            "top_terms_by_doc_freq": [(w, int(d)) for w, d in top_df],
            "example_passage_title": sample["title"],
            "example_passage_vector_top10": passage_vector,
        },
        "light_stemming": {
            "vocab_before": len(vocab_raw),
            "vocab_after_prefix_strip": len(vocab_stem),
            "reduction_pct": round(100 * (1 - len(vocab_stem) / len(vocab_raw)), 1),
            "examples": {w: light_stem(w) for w in
                         ["דמי", "לעובדים", "והמעסיק", "כשעובד", "בתקופת", "מהמוסד"]},
        },
    }

    out = os.path.join(config.RESULTS_DIR, "corpus_stats.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"\n[corpus-stats] -> {out}")
    return stats


if __name__ == "__main__":
    main()
