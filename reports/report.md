# Hebrew Semantic Retrieval for Social-Rights Questions
### Bridging everyday language and official phrasing with NLP

**Author:** Yanik Gutia (318553526) · **Track 3 — Data-Driven NLP** · HIT · Dr. Igor Kleiner

> *Max 5 pages. Numbers marked `[Colab]` are filled from the run of
> `notebooks/NLP_Project.ipynb`, which prints a ready-to-paste metrics table.*

---

## 1. Introduction & Research Question
Israelis seeking social rights (benefits, allowances, bureaucratic procedures) ask questions in
**everyday language** — *"מה מגיע לי אחרי לידה?"* — while official sources are written in
**formal, legal-administrative Hebrew**. This vocabulary gap makes simple keyword search miss
relevant pages.

**Research question.** To what extent does **semantic** retrieval based on Hebrew sentence
embeddings (AlephBERT) improve information finding in the rights domain compared to classic
**lexical** retrieval (TF-IDF)? And does a **hybrid** of the two improve further?

**Hypotheses.** (H1) Semantic retrieval beats lexical on high *phrasing-gap* queries.
(H2) A hybrid beats either single method on ranking-quality metrics (MRR, nDCG).

## 2. Data
A self-collected corpus (no Kaggle), from two public sources (full details in `DATA.md`):
* **Kol-Zchut** (CC-BY-SA), via the official **MediaWiki API** — clean plain-text extracts
  across six life-domains: disability, unemployment, health, family, income-support, parenting.
* **Bituach Leumi** — a small curated set of benefit pages, scraped robots-aware from the
  `#mainContent` region.

Pages are cleaned (niqqud stripped, boilerplate removed) and **chunked** into ≤600-char passages.
Snapshot used: **≈296 documents → ≈1,602 passages** (`data/processed/corpus.jsonl`).

**Evaluation set.** 40 hand-authored colloquial questions, each mapped to ground-truth
document(s) and tagged with a `phrasing_gap` of low/medium/high. Scoring is at **document level**:
a hit is a returned chunk whose parent document is in the gold set.

## 3. Methods
A shared retriever interface (`src/retrievers.py`) with five models:

| Model | Type | Idea |
|------|------|------|
| **TF-IDF** | lexical (baseline) | sparse cosine; Hebrew tokens + stopwords, 1–2-grams |
| **BM25** | lexical (bonus) | Okapi BM25 ranking |
| **AlephBERT** | semantic | `imvladikon/sentence-transformers-alephbert`, dense cosine |
| **Hybrid-RRF** | fusion | Reciprocal Rank Fusion of TF-IDF + semantic |
| **Hybrid-weighted** | fusion | min-max score fusion (α·semantic + (1-α)·lexical) |

Passage embeddings are computed once and cached. **Metrics:** Recall@{1,3,5,10}, **MRR**,
**nDCG@10**, **MAP** (implemented from their definitions in `src/evaluate.py`).

## 4. Results

**Main table** (`results/metrics.csv`):

| Retriever | R@1 | R@3 | R@5 | R@10 | MRR | nDCG@10 | MAP |
|-----------|-----|-----|-----|------|-----|---------|-----|
| TF-IDF | `[Colab]` | | | | | | |
| BM25 | `[Colab]` | | | | | | |
| AlephBERT (semantic) | `[Colab]` | | | | | | |
| Hybrid (RRF) | `[Colab]` | | | | | | |
| Hybrid (weighted) | `[Colab]` | | | | | | |

**Figures** (`results/figures/`):
* `metrics_bar.png` — Recall@k & MRR per retriever.
* `recall_curve.png` — Recall@k vs k.
* `winloss_heatmap.png` — per-query first-hit rank, lexical vs semantic.
* `embedding_tsne.png` — t-SNE of passage embeddings, colored by domain (clusters by life-domain).

**Reading the results.** Report whether semantic leads on R@1/MRR (meaning bias) while lexical
holds on exact-term queries, and whether the hybrid tops the ranking metrics (expected from H2).
Break Recall@1 down by `phrasing_gap` (from `results/per_query.csv`) to test H1 directly: the
semantic advantage should grow as the gap widens.

## 5. Error Analysis
`results/error_analysis.md` documents ≥10 worked examples in three buckets:
* **A — semantic wins / lexical fails:** synonymy and colloquial→formal gaps (e.g. *"פיטרו אותי"*
  vs the formal *"דמי אבטלה / זכאות"*); embeddings bridge zero word-overlap.
* **B — lexical wins / semantic fails:** a rare, distinctive term gives the sparse model a sharp
  signal the embedding diffuses.
* **C — both fail:** sparse corpus coverage or ambiguous phrasing.

Each example shows both models' top-3, the gold rank, and an automatic diagnosis from the
`phrasing_gap` tag and query↔title word overlap.

## 6. Limitations & Ethics
Small single-annotator eval set (indicative, not tight); six-domain coverage; Hebrew morphology
penalizes lexical models; AlephBERT may carry pre-training social biases. The system is a
**research prototype, not legal advice** — a real deployment must show source links and a
disclaimer. Full statement in `ETHICS.md`; data licensing in `DATA.md`.

## 7. Conclusion
The project delivers a complete Hebrew IR pipeline and a controlled comparison of lexical,
semantic, and hybrid retrieval for a real social problem. The hybrid approach is the practical
recommendation: it combines lexical precision with the semantic model's tolerance of everyday
phrasing. Future work: Hebrew lemmatization, a larger graded eval set, and a retrieval-tuned
multilingual baseline (E5) to isolate Hebrew-specific from retrieval-tuned effects.

## 8. AI Usage Disclosure (summary)
AI tools were used only as support (scaffolding, docstrings, debugging help, metric-definition
clarification). All code was rewritten/edited, executed, and verified by the author, who can
explain every part. Full table in `AI_USAGE.md`.

*Personal reflection, failure log, and work log: see `REFLECTION.md`.*
