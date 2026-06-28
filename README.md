# הנגשת זכויות חברתיות באמצעות NLP — Hebrew Semantic Rights Retrieval

A Hebrew **information-retrieval** system that answers free-text questions about social rights,
benefits and bureaucracy (e.g. *"מה מגיע לי אחרי לידה?"*) by finding the most relevant passages
from a self-collected corpus of **Kol-Zchut** and **Bituach Leumi** content.

It compares **lexical** retrieval (TF-IDF, BM25), **semantic** retrieval (Hebrew AlephBERT
sentence embeddings), and a **hybrid** of the two — and asks whether semantics, and then fusion,
improve finding information across the everyday-language ↔ formal-language gap.

> **Track 3 — Data-Driven NLP** · HIT · Dr. Igor Kleiner · Author: Yanik Gotie (318553526)

## Research question
Does sentence-embedding semantic retrieval improve information finding for Hebrew rights
questions vs. classic TF-IDF — and does a lexical+semantic hybrid improve further?

## Architecture
```
scrape (Kol-Zchut API + Bituach Leumi HTML)
   └─> clean + chunk  ──> data/processed/corpus.jsonl   (≈296 docs → ≈1,602 passages)
                          data/processed/eval_set.json  (40 questions + ground truth)
   ┌──────────────── retrievers (shared interface) ────────────────┐
   │ TF-IDF │ BM25 │ AlephBERT (semantic) │ Hybrid-RRF │ Hybrid-wtd │
   └───────────────────────────────────────────────────────────────┘
            └─> evaluate (Recall@k, MRR, nDCG, MAP) ─> results/metrics.csv
            └─> error analysis (≥10 cases)          ─> results/error_analysis.md
            └─> visualize (4 figures)               ─> results/figures/*.png
```

## Quickstart

### Google Colab (recommended)
Open `notebooks/NLP_Project.ipynb` → *Runtime ▸ Run all*. Colab has open internet (the
AlephBERT model downloads from HuggingFace) and a free GPU. The notebook produces every result
and figure inline.

### Local
```bash
pip install -r requirements.txt
python src/run_all.py            # scrape (cached) → corpus → retrievers → eval → figures
```
> If your network blocks HuggingFace, the semantic model can't download locally — use Colab.
> `python src/run_all.py --allow-offline` runs the rest with a non-semantic stand-in (plumbing
> test only; not meaningful results).

## Repository layout
```
config.py                 # central paths, sources, model name, k-values
src/
  scrape_kolzchut.py      # Kol-Zchut via MediaWiki API
  scrape_btl.py           # Bituach Leumi HTML scrape (robots-aware)
  preprocess.py           # Hebrew normalization + chunking + stopwords
  build_corpus.py         # merge + chunk -> corpus.jsonl
  retrievers.py           # TF-IDF, BM25, AlephBERT semantic, Hybrid (RRF/weighted)
  evaluate.py             # Recall@k, MRR, nDCG@10, MAP
  splits.py               # query-level train(index)/validation/test split
  eval_splits.py          # per-split metrics -> results/metrics_by_split.csv
  error_analysis.py       # >=10 worked examples, lexical vs semantic
  corpus_stats.py         # classical-NLP stats (tokens, stopwords, TF-IDF, n-grams)
  visualize.py            # 4 figures
  run_all.py              # end-to-end orchestrator
notebooks/
  NLP_Project.ipynb              # clean, Colab-ready source
  NLP_Project_collab_run2.ipynb  # executed Colab run with outputs
data/{raw,processed}/     # cached pulls + corpus + eval set
results/                  # metrics.csv, per_query.csv, error_analysis.md, figures/
reports/                  # report.md (≤5 pp) + presentation.pptx
AI_USAGE.md  REFLECTION.md  ETHICS.md  DATA.md
```

## Course deliverables checklist
- [x] Python implementation, reproducible, clear train/eval split (held-out eval set)
- [x] ≥2 modeling approaches (5: TF-IDF, BM25, AlephBERT, 2× hybrid)
- [x] ≥2 evaluation metrics (Recall@k, MRR, nDCG, MAP)
- [x] Error analysis (≥10 examples) · ≥2 visualizations (4 figures)
- [x] AI_USAGE.md · REFLECTION.md · ETHICS.md · DATA.md
- [x] Report (`reports/report.md`, ≤5 pp) · Slides (`reports/presentation.pptx`)
- [x] No Kaggle; original self-collected Hebrew corpus

## License / data
Code: academic course project. Data: Kol-Zchut (CC-BY-SA, attributed) + Bituach Leumi (public
official info). See `DATA.md` and `ETHICS.md`.
