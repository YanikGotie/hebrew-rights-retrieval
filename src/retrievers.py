"""
Retrieval models with a shared interface.

Every retriever implements:
    .index(corpus)            # corpus = list of chunk dicts from build_corpus.load_corpus
    .search(query, k) -> [hit, ...]
where each hit is {"chunk_id","doc_id","title","url","domain","score","rank"}.

Implemented:
  * TfidfRetriever     — sparse lexical baseline (sklearn TF-IDF + cosine).
  * BM25Retriever      — Okapi BM25 lexical baseline (rank_bm25), bonus comparison.
  * SemanticRetriever  — Hebrew sentence embeddings (AlephBERT), cosine over dense vectors.
  * HybridRetriever    — fuses a lexical + a semantic retriever via Reciprocal Rank
                         Fusion (default) or weighted min-max score fusion.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
import preprocess  # noqa: E402


# -----------------------------------------------------------------------------
# Base
# -----------------------------------------------------------------------------
class BaseRetriever:
    name = "base"

    def __init__(self):
        self.corpus = []

    def index(self, corpus):
        self.corpus = corpus
        return self

    def _hit(self, idx, score, rank):
        r = self.corpus[idx]
        return {
            "chunk_id": r["chunk_id"],
            "doc_id": r["doc_id"],
            "title": r["title"],
            "url": r["url"],
            "domain": r["domain"],
            "score": float(score),
            "rank": rank,
        }

    def _topk(self, scores, k):
        k = min(k, len(scores))
        # argpartition for speed, then sort the top-k slice
        idx = np.argpartition(-scores, k - 1)[:k]
        idx = idx[np.argsort(-scores[idx])]
        return [self._hit(i, scores[i], r + 1) for r, i in enumerate(idx)]

    def search(self, query, k=10):  # pragma: no cover - overridden
        raise NotImplementedError


# -----------------------------------------------------------------------------
# Lexical: TF-IDF
# -----------------------------------------------------------------------------
class TfidfRetriever(BaseRetriever):
    name = "tfidf"

    def __init__(self, ngram_range=(1, 2), min_df=2):
        super().__init__()
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.vectorizer = TfidfVectorizer(
            ngram_range=ngram_range,
            min_df=min_df,
            token_pattern=r"(?u)\b\w+\b",
            stop_words=preprocess.HEB_STOPWORDS,
            sublinear_tf=True,
        )
        self.matrix = None

    def index(self, corpus):
        super().index(corpus)
        self.matrix = self.vectorizer.fit_transform([r["text_norm"] for r in corpus])
        return self

    def search(self, query, k=10):
        from sklearn.metrics.pairwise import linear_kernel

        qv = self.vectorizer.transform([preprocess.normalize_for_index(query)])
        scores = linear_kernel(qv, self.matrix).ravel()  # tf-idf rows are L2-normalized
        return self._topk(scores, k)


# -----------------------------------------------------------------------------
# Lexical: BM25 (bonus baseline)
# -----------------------------------------------------------------------------
class BM25Retriever(BaseRetriever):
    name = "bm25"

    def __init__(self):
        super().__init__()
        self.bm25 = None

    def index(self, corpus):
        from rank_bm25 import BM25Okapi

        super().index(corpus)
        stop = set(preprocess.HEB_STOPWORDS)
        tokens = [[t for t in r["text_norm"].split() if t not in stop] for r in corpus]
        self.bm25 = BM25Okapi(tokens)
        return self

    def search(self, query, k=10):
        stop = set(preprocess.HEB_STOPWORDS)
        q = [t for t in preprocess.normalize_for_index(query).split() if t not in stop]
        scores = np.asarray(self.bm25.get_scores(q))
        return self._topk(scores, k)


# -----------------------------------------------------------------------------
# Semantic: Hebrew sentence embeddings (AlephBERT)
# -----------------------------------------------------------------------------
class SemanticRetriever(BaseRetriever):
    name = "semantic"

    def __init__(self, model_name=None, batch_size=32, use_cache=True):
        super().__init__()
        self.model_name = model_name or config.SEMANTIC_MODEL_NAME
        self.batch_size = batch_size
        self.use_cache = use_cache
        self.model = None
        self.embeddings = None

    def _load_model(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer

            device = self._device()
            print(f"[semantic] loading {self.model_name} on {device}")
            self.model = SentenceTransformer(self.model_name, device=device)
        return self.model

    @staticmethod
    def _device():
        import torch

        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"

    @staticmethod
    def _passage_text(r):
        # Title carries strong topical signal; prepend it to each chunk.
        return f"{r['title']}. {r['text']}"

    def index(self, corpus):
        super().index(corpus)
        ids = [r["chunk_id"] for r in corpus]

        if self.use_cache and self._cache_valid(ids):
            self.embeddings = np.load(config.EMBEDDINGS_PATH)
            print(f"[semantic] loaded cached embeddings {self.embeddings.shape}")
            return self

        model = self._load_model()
        texts = [self._passage_text(r) for r in corpus]
        print(f"[semantic] encoding {len(texts)} passages...")
        self.embeddings = model.encode(
            texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        ).astype(np.float32)
        if self.use_cache:
            np.save(config.EMBEDDINGS_PATH, self.embeddings)
            with open(config.EMBEDDINGS_IDS_PATH, "w", encoding="utf-8") as f:
                json.dump({"model": self.model_name, "ids": ids}, f, ensure_ascii=False)
        return self

    def _cache_valid(self, ids):
        if not (os.path.exists(config.EMBEDDINGS_PATH) and os.path.exists(config.EMBEDDINGS_IDS_PATH)):
            return False
        meta = json.load(open(config.EMBEDDINGS_IDS_PATH, encoding="utf-8"))
        return meta.get("model") == self.model_name and meta.get("ids") == ids

    def search(self, query, k=10):
        model = self._load_model()
        qv = model.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True
        ).astype(np.float32)[0]
        scores = self.embeddings @ qv  # cosine (both normalized)
        return self._topk(scores, k)


# -----------------------------------------------------------------------------
# Hybrid: fuse lexical + semantic
# -----------------------------------------------------------------------------
class HybridRetriever(BaseRetriever):
    """Fuse a lexical and a semantic retriever.

    method="rrf"      Reciprocal Rank Fusion: score = sum 1/(RRF_K + rank).
    method="weighted" min-max normalize each retriever's scores, then
                      alpha*semantic + (1-alpha)*lexical.
    """

    def __init__(self, lexical, semantic, method="rrf", alpha=None, rrf_k=None, pool=50):
        super().__init__()
        self.lexical = lexical
        self.semantic = semantic
        self.method = method
        self.alpha = config.HYBRID_ALPHA if alpha is None else alpha
        self.rrf_k = config.RRF_K if rrf_k is None else rrf_k
        self.pool = pool
        self.name = f"hybrid_{method}"

    def index(self, corpus):
        super().index(corpus)
        # assume sub-retrievers already indexed on the same corpus
        return self

    @staticmethod
    def _minmax(d):
        if not d:
            return {}
        vals = list(d.values())
        lo, hi = min(vals), max(vals)
        if hi - lo < 1e-12:
            return {k: 0.0 for k in d}
        return {k: (v - lo) / (hi - lo) for k, v in d.items()}

    def search(self, query, k=10):
        lex = self.lexical.search(query, self.pool)
        sem = self.semantic.search(query, self.pool)

        if self.method == "rrf":
            fused = {}
            for hits in (lex, sem):
                for h in hits:
                    fused[h["chunk_id"]] = fused.get(h["chunk_id"], 0.0) + 1.0 / (
                        self.rrf_k + h["rank"]
                    )
        else:  # weighted score fusion
            lex_s = self._minmax({h["chunk_id"]: h["score"] for h in lex})
            sem_s = self._minmax({h["chunk_id"]: h["score"] for h in sem})
            fused = {}
            for cid in set(lex_s) | set(sem_s):
                fused[cid] = self.alpha * sem_s.get(cid, 0.0) + (1 - self.alpha) * lex_s.get(cid, 0.0)

        meta = {h["chunk_id"]: h for h in lex + sem}
        ranked = sorted(fused.items(), key=lambda kv: -kv[1])[:k]
        out = []
        for rank, (cid, score) in enumerate(ranked, 1):
            h = dict(meta[cid])
            h["score"], h["rank"] = float(score), rank
            out.append(h)
        return out


class OfflineHashingRetriever(BaseRetriever):
    """Deterministic, network-free stand-in for the semantic retriever.

    Used ONLY for local smoke-testing of the full pipeline when HuggingFace is
    unreachable (e.g. behind a corporate firewall). It produces dense, L2-normalized
    char-n-gram vectors so every downstream stage (hybrid fusion, t-SNE, evaluation,
    error analysis) can be exercised. It is NOT a real language model and is never
    used in Colab, where the genuine AlephBERT model loads. Quality is not meaningful.
    """

    name = "semantic"  # mimics the semantic slot so downstream code is unchanged

    def __init__(self, n_features=512):
        super().__init__()
        from sklearn.feature_extraction.text import HashingVectorizer

        self.vectorizer = HashingVectorizer(
            analyzer="char_wb", ngram_range=(3, 5), n_features=n_features, norm="l2"
        )
        self.embeddings = None

    def index(self, corpus):
        super().index(corpus)
        texts = [f"{r['title']}. {r['text']}" for r in corpus]
        self.embeddings = self.vectorizer.transform(texts).toarray().astype(np.float32)
        return self

    def search(self, query, k=10):
        qv = self.vectorizer.transform([query]).toarray().astype(np.float32)[0]
        scores = self.embeddings @ qv
        return self._topk(scores, k)


def build_all(corpus, include_bm25=True, offline_fallback=False):
    """Construct and index the full retriever suite on a shared corpus."""
    tfidf = TfidfRetriever().index(corpus)
    try:
        semantic = SemanticRetriever().index(corpus)
    except Exception as e:
        if not offline_fallback:
            raise
        print(
            f"[retrievers] semantic model unavailable ({type(e).__name__}); "
            "using OFFLINE stand-in encoder (results not meaningful — local smoke test only)."
        )
        semantic = OfflineHashingRetriever().index(corpus)
    retrievers = {"tfidf": tfidf, "semantic": semantic}
    if include_bm25:
        retrievers["bm25"] = BM25Retriever().index(corpus)
    retrievers["hybrid_rrf"] = HybridRetriever(tfidf, semantic, method="rrf").index(corpus)
    retrievers["hybrid_weighted"] = HybridRetriever(
        tfidf, semantic, method="weighted"
    ).index(corpus)
    return retrievers
