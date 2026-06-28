# Hebrew Semantic Retrieval for Social-Rights Questions
### Bridging everyday language and official phrasing with NLP

**Author:** Yanik Gotie (318553526) · **Track 3 — Data-Driven NLP** · HIT · Dr. Igor Kleiner

---

## 1. Introduction & Research Question
Israelis seeking social rights (benefits, allowances, bureaucratic procedures) ask questions in
**everyday language** — *"פיטרו אותי, מה מגיע לי?"* — while official sources are written in
**formal, legal-administrative Hebrew** (*"זכאות לדמי אבטלה"*). This vocabulary gap makes simple
keyword search miss relevant pages.

**Research question.** Does **semantic** retrieval with Hebrew sentence embeddings (AlephBERT)
improve information finding in the rights domain over classic **lexical** retrieval (TF-IDF) — and
does a **hybrid** of the two improve further?

**Hypotheses.** (H1) Semantic beats lexical on high *phrasing-gap* queries.
(H2) A hybrid beats either single method on ranking-quality metrics (MRR, nDCG).

## 2. Data
A self-collected corpus (no Kaggle), from two public sources (details in `DATA.md`):
* **Kol-Zchut** (CC-BY-SA), via the official **MediaWiki API** — clean plain-text extracts across
  six life-domains: disability, unemployment, health, family, income-support, parenting.
* **Bituach Leumi** — a small curated set of benefit pages, scraped robots-aware from `#mainContent`.

Pages are cleaned (niqqud stripped, boilerplate removed) and **chunked** into ≤600-char passages.
**Snapshot: 296 documents → 1,602 passages → 122,928 tokens** (`data/processed/corpus.jsonl`).

**Evaluation set.** 40 hand-authored colloquial questions, each mapped to ground-truth document(s)
and tagged with a `phrasing_gap` (low/medium/high). Scoring is at **document level**: a hit is a
returned chunk whose parent document is in the gold set.

## 3. Methods

### 3.1 Classical NLP preprocessing
Each passage is run through a classical pipeline before lexical indexing:
* **Normalization** — strip niqqud (`[֑-ׇ]`), drop punctuation/Latin, lowercase, collapse spaces.
* **Tokenization** — whitespace/word tokens (`\b\w+\b`).
* **Stop-word removal** — a 94-word Hebrew function-word list (pronouns, prepositions, question
  words). Example: a 33-token passage → 26 content tokens after removing *או, מי, וכן, כדי, על, עד*.
* **Vectorization (TF-IDF)** — 1–2-grams, `min_df=2`, sublinear TF, L2-normalized.
  The corpus becomes a **1,602 × 20,981** matrix (7,323 unigrams + 13,658 bigrams), **99.58 % sparse**
  (only 141,493 non-zeros). Top terms by document frequency: *לביטוח, לאומי, הכנסה, עבודה, נכות*, and
  the bigram *"לביטוח לאומי"* (264 docs).
* **Morphology note.** Hebrew glues particles (ב/ל/מ/ה/ו/ש/כ) to words, inflating the vocabulary.
  A light prefix-stripping experiment shrinks the raw vocabulary **13,415 → 8,963 types (−33 %)** —
  evidence that morphology, not topic, drives much of the sparsity. We kept full forms for the main
  results (no reliable offline Hebrew lemmatizer) and flag lemmatization as future work.

### 3.2 Retrievers (≥2 required → five built)
| Model | Type | Idea |
|------|------|------|
| **TF-IDF** | lexical (baseline) | sparse cosine over the matrix above |
| **BM25** | lexical (bonus) | Okapi BM25 ranking |
| **AlephBERT** | semantic | `imvladikon/sentence-transformers-alephbert`, dense cosine |
| **Hybrid-RRF** | fusion | Reciprocal Rank Fusion of TF-IDF + semantic |
| **Hybrid-weighted** | fusion | min-max score fusion (α·semantic + (1-α)·lexical) |

Passage embeddings are computed once and cached. **Metrics:** Recall@{1,3,5,10}, **MRR**,
**nDCG@10**, **MAP**, implemented from their definitions in `src/evaluate.py`.

### 3.3 Train / validation / test protocol
This is retrieval, so the split is **query-level** (`src/splits.py`):
* **"Train" / index = the corpus** — the lexical models fit their vocabulary + IDF on it and
  the semantic model encodes it; **no ground-truth labels are used here**.
* The **40 labeled queries** are split, **stratified by domain, seed 42**, into
  **validation/dev (14, 35%)** and **held-out test (26, 65%)** — written to
  `data/processed/eval_split.json`.
* No hyper-parameters were tuned on the labeled queries (defaults RRF *k*=60, fusion α=0.5), so
  the split is an **unbiased robustness check**: does the full-set finding survive on queries that
  influenced no choice? Splitting at the query level (not the chunk level) is what prevents leakage.

## 4. Results

| Retriever | R@1 | R@3 | R@5 | R@10 | MRR | nDCG@10 | MAP |
|-----------|----:|----:|----:|-----:|----:|--------:|----:|
| TF-IDF | 0.475 | 0.725 | 0.825 | 0.850 | 0.618 | 0.649 | 0.588 |
| BM25 | 0.500 | 0.650 | 0.825 | 0.875 | 0.612 | 0.647 | 0.578 |
| AlephBERT (semantic) | 0.475 | 0.700 | 0.725 | 0.775 | 0.579 | 0.597 | 0.540 |
| **Hybrid (RRF)** | **0.550** | **0.750** | 0.800 | **0.875** | **0.668** | **0.704** | **0.652** |
| Hybrid (weighted) | 0.550 | 0.725 | 0.800 | 0.850 | 0.653 | 0.681 | 0.632 |

Figures in `results/figures/`: `metrics_bar.png`, `recall_curve.png`, `winloss_heatmap.png`,
`embedding_tsne.png`. Table above = full 40 queries; the **held-out test** numbers below
(`results/metrics_by_split.csv`) confirm the ranking on unseen queries.

**Held-out test set (26 queries) — MRR:** Hybrid-RRF **0.690** · Hybrid-wtd 0.659 ·
BM25 0.606 · TF-IDF 0.603 · AlephBERT 0.585. The hybrid lead is *larger* on the held-out test
than on the full set, so it is not an artifact of evaluating on the selection data.

**Recall@1 by phrasing-gap** (H1 test):

| gap | n | TF-IDF | AlephBERT | Hybrid-RRF |
|-----|--:|------:|----------:|-----------:|
| low | 4 | 0.25 | 0.50 | 0.75 |
| medium | 11 | 0.55 | 0.55 | 0.64 |
| high | 25 | 0.48 | **0.44** | 0.48 |

**Misses (gold not in top-10):** TF-IDF 6/40 · AlephBERT 9/40 · Hybrid-RRF 5/40.

**Findings.**
* **H2 — supported.** The **Hybrid (RRF)** is the best model on every ranking metric (MRR 0.668,
  nDCG 0.704, MAP 0.652), ties for best Recall@10 (0.875), and misses the fewest queries (5).
* **H1 — not supported (the interesting result).** AlephBERT **alone is the weakest** single model
  (MRR 0.579, 9 misses) and does **not** beat lexical on high-gap queries (0.44 vs 0.48). A Hebrew
  sentence encoder derived from a masked LM — not contrastively fine-tuned for retrieval — produces
  *noisier* similarities than a sharp lexical match in this term-heavy, domain-specific corpus.
* **Why the hybrid still wins.** The semantic model makes *different* errors: it rescues zero-overlap
  paraphrases lexical cannot (e.g. *"פיטרו אותי, מה מגיע לי?"* → *דמי אבטלה*, gold rank 11→1). Fusing
  the two keeps lexical precision **and** semantic recall — complementarity, not superiority.

## 5. Error Analysis
`results/error_analysis.md` documents 16 worked examples: **4 semantic-wins, 5 lexical-wins, 7 both-fail.**
* **A — semantic wins / lexical fails:** zero/low word-overlap paraphrases (*"חייבים להגיע ללשכת
  התעסוקה כל הזמן?"* → *התייצבות בשירות התעסוקה*); embeddings bridge the gap.
* **B — lexical wins / semantic fails:** a rare distinctive term gives TF-IDF a sharp signal the
  embedding diffuses (*"כיסא גלגלים ומכשירי שיקום"* → exact title; semantic misses).
* **C — both fail:** corpus-coverage gaps / ambiguity (*"איך מקבלים קצבת נכות?"* — the closest page
  is a Bituach-Leumi stub, drowned by many specific *קביעת נכות בגין…* pages).

## 6. Limitations & Ethics
Small single-annotator eval set (indicative, not tight); six-domain coverage; Hebrew morphology
penalizes the lexical models; AlephBERT may carry pre-training social biases. The system is a
**research prototype, not legal advice** — a real deployment must show source links and a disclaimer.
Full statement in `ETHICS.md`; data licensing in `DATA.md`.

## 7. Conclusion
A complete Hebrew IR pipeline with a controlled comparison of lexical, semantic, and hybrid retrieval
for a real social problem. The practical recommendation is the **hybrid**: it combines lexical
precision with the semantic model's tolerance of everyday phrasing, and is the only model that beats
both baselines. The headline lesson is that an off-the-shelf Hebrew embedding model is **not** a free
win for retrieval — but it is a useful *complement*. Future work: a retrieval-tuned model (e.g. E5),
Hebrew lemmatization, and a larger graded evaluation set.

## 8. AI Usage
An AI assistant was used as a **code-writing helper** (boilerplate, docstrings, debugging). All code
was reviewed, executed, and is fully understood by the author. See `AI_USAGE.md`.

*Personal reflection, failure log, and work log: `REFLECTION.md`.*
