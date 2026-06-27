"""
Generate the project's figures into results/figures/.

  1. metrics_bar.png        — Recall@k & MRR per retriever (grouped bars).
  2. recall_curve.png       — Recall@k vs k for each retriever.
  3. winloss_heatmap.png    — per-query first-hit rank, lexical vs semantic (the
                              "where does each model win" view).
  4. embedding_tsne.png     — t-SNE of passage embeddings colored by life-domain
                              (shows the semantic space the retriever searches).

Hebrew labels are reshaped for correct RTL display in matplotlib.
"""
from __future__ import annotations

import os
import sys

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402

plt.rcParams.update({"figure.dpi": 130, "font.size": 11, "axes.grid": True, "grid.alpha": 0.3})

# Friendly display names / colors for retrievers.
NICE = {
    "tfidf": "TF-IDF",
    "bm25": "BM25",
    "semantic": "AlephBERT (semantic)",
    "hybrid_rrf": "Hybrid (RRF)",
    "hybrid_weighted": "Hybrid (weighted)",
}
DOMAIN_HE = {
    "disability": "נכות",
    "unemployment": "אבטלה",
    "health": "בריאות",
    "family": "ילדים ונוער",
    "welfare": "הבטחת הכנסה",
    "parenting": "הורות",
    "elderly": "אזרחים ותיקים",
}


def _rtl(text):
    """Best-effort RTL reshaping so Hebrew renders correctly in matplotlib."""
    try:
        import arabic_reshaper  # noqa: F401  (optional)
        from bidi.algorithm import get_display

        return get_display(text)
    except Exception:
        # Fallback: reverse so Hebrew at least reads right-to-left visually.
        return text[::-1]


def fig_metrics_bar(metrics_df):
    cols = [c for c in metrics_df.columns if c.startswith("recall@")] + ["mrr"]
    retr = list(metrics_df.index)
    x = np.arange(len(cols))
    width = 0.8 / len(retr)
    fig, ax = plt.subplots(figsize=(10, 5))
    for i, r in enumerate(retr):
        ax.bar(x + i * width, metrics_df.loc[r, cols].values, width, label=NICE.get(r, r))
    ax.set_xticks(x + width * (len(retr) - 1) / 2)
    ax.set_xticklabels([c.upper() for c in cols])
    ax.set_ylabel("score")
    ax.set_ylim(0, 1)
    ax.set_title("Retrieval quality by metric")
    ax.legend(fontsize=9)
    _save(fig, "metrics_bar.png")


def fig_recall_curve(metrics_df):
    ks = sorted(int(c.split("@")[1]) for c in metrics_df.columns if c.startswith("recall@"))
    fig, ax = plt.subplots(figsize=(8, 5))
    for r in metrics_df.index:
        ys = [metrics_df.loc[r, f"recall@{k}"] for k in ks]
        ax.plot(ks, ys, marker="o", label=NICE.get(r, r))
    ax.set_xlabel("k")
    ax.set_ylabel("Recall@k")
    ax.set_xticks(ks)
    ax.set_ylim(0, 1)
    ax.set_title("Recall@k vs. k")
    ax.legend(fontsize=9)
    _save(fig, "recall_curve.png")


def fig_winloss_heatmap(per_query_df, lexical="tfidf", semantic="semantic"):
    """First-hit rank per query for lexical vs semantic (lower = better; blank = miss)."""
    piv = per_query_df.pivot_table(
        index="qid", columns="retriever", values="first_hit_rank", aggfunc="first"
    )
    for c in (lexical, semantic):
        if c not in piv:
            piv[c] = np.nan
    piv = piv[[lexical, semantic]].apply(pd.to_numeric, errors="coerce")
    order = per_query_df.drop_duplicates("qid").set_index("qid")["domain"]
    piv = piv.loc[[q for q in order.index if q in piv.index]]

    data = piv.values.astype(float)
    fig, ax = plt.subplots(figsize=(5.5, max(6, 0.28 * len(piv))))
    masked = np.ma.masked_invalid(data)
    cmap = plt.cm.RdYlGn_r
    cmap.set_bad("lightgray")
    im = ax.imshow(masked, cmap=cmap, vmin=1, vmax=10, aspect="auto")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["TF-IDF", "AlephBERT"])
    ax.set_yticks(range(len(piv)))
    ax.set_yticklabels(piv.index, fontsize=7)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = data[i, j]
            ax.text(j, i, "–" if np.isnan(v) else int(v), ha="center", va="center", fontsize=7)
    ax.set_title("First-hit rank per query\n(green=top, gray=missed)")
    fig.colorbar(im, ax=ax, label="rank of first relevant doc")
    _save(fig, "winloss_heatmap.png")


def fig_embedding_tsne(corpus, embeddings):
    from sklearn.manifold import TSNE

    domains = [r["domain"] for r in corpus]
    uniq = sorted(set(domains))
    perplexity = min(30, max(5, len(corpus) // 50))
    xy = TSNE(
        n_components=2, perplexity=perplexity, init="pca",
        random_state=config.RANDOM_SEED, max_iter=1000,
    ).fit_transform(embeddings)

    fig, ax = plt.subplots(figsize=(9, 7))
    cmap = plt.cm.tab10
    for i, dom in enumerate(uniq):
        idx = [j for j, d in enumerate(domains) if d == dom]
        ax.scatter(xy[idx, 0], xy[idx, 1], s=12, alpha=0.6, color=cmap(i % 10),
                   label=_rtl(DOMAIN_HE.get(dom, dom)))
    ax.set_title("t-SNE of AlephBERT passage embeddings, colored by domain")
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    ax.legend(fontsize=9, loc="best")
    _save(fig, "embedding_tsne.png")


def _save(fig, name):
    path = os.path.join(config.FIGURES_DIR, name)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"[viz] saved {path}")


def run(metrics_df, per_query_df, corpus=None, embeddings=None):
    fig_metrics_bar(metrics_df)
    fig_recall_curve(metrics_df)
    fig_winloss_heatmap(per_query_df)
    if corpus is not None and embeddings is not None:
        fig_embedding_tsne(corpus, embeddings)


if __name__ == "__main__":
    import build_corpus
    import retrievers as R

    metrics_df = pd.read_csv(config.METRICS_PATH, index_col=0)
    per_query_df = pd.read_csv(config.PERQUERY_PATH)
    corpus = build_corpus.load_corpus()
    sem = R.SemanticRetriever().index(corpus)
    run(metrics_df, per_query_df, corpus, sem.embeddings)
