# REFLECTION.md — Personal Reflection & Technical Ownership

> Solo project (approved as an individual submission). The work log below is for one author.

## What I personally implemented
I built the whole pipeline end-to-end:
* The **data layer** — a MediaWiki-API collector for Kol-Zchut (`src/scrape_kolzchut.py`), a
  robots-aware HTML scraper for Bituach Leumi (`src/scrape_btl.py`), and the Hebrew
  preprocessing + chunking (`src/preprocess.py`, `src/build_corpus.py`).
* The **modeling layer** — a shared retriever interface with TF-IDF, BM25, an AlephBERT
  semantic retriever, and two hybrid fusions (RRF and weighted) in `src/retrievers.py`.
* The **evaluation layer** — Recall@k, MRR, nDCG and MAP implemented from their definitions
  (`src/evaluate.py`), plus the automatic error analysis (`src/error_analysis.py`) and the
  figures (`src/visualize.py`).
* The **40-question evaluation set**, written by hand by reading candidate documents and
  tagging each query with how far its wording sits from the official phrasing.

## Failure log (concrete things that broke and how I fixed them)
1. **The corpus silently shrank to ~16 pages.** My first Kol-Zchut collector batched many
   page-ids into one `extracts` API call. The MediaWiki *TextExtracts* extension caps
   `exlimit` at **1** whenever full-page text is requested, so only the first page in each
   batch came back — and the rest were dropped without an error. I found it by printing the
   ratio of requested-to-returned pages. **Fix:** fetch one page per request (full text
   guaranteed), with progress logging. The corpus went from 16 → ~296 documents.
2. **The lexical baseline looked absurdly bad.** Short colloquial queries like
   *"פיטרו אותי, מה מגיע לי?"* were dominated by function words, so TF-IDF matched unrelated
   "letter/template" pages. I almost concluded "TF-IDF is useless," which would have been an
   unfair baseline. **Fix:** added a curated Hebrew stopword list (used by both TF-IDF and
   BM25). The baseline became competitive — and the comparison became honest.
3. **HuggingFace was blocked on my network.** The semantic model would not download (the
   corporate firewall classifies HuggingFace as a "Generative AI tool"). **Fix:** I made the
   project **Colab-first** for the semantic stage (open internet + free GPU), cached the
   passage embeddings so re-runs are instant, and added an explicit offline stand-in encoder
   (`--allow-offline`) purely to keep the rest of the pipeline testable. This separation also
   made the embedding cost a one-time step.

## Technical challenges
* **Hebrew morphology & the formal-vs-colloquial gap** — the whole reason the project exists.
  Rich inflection and attached particles mean exact-term matching misses paraphrases; deciding
  *not* to fold final-letter forms (it didn't help and risked merging tokens) was a deliberate,
  measured call.
* **Heterogeneous sources** — Kol-Zchut's clean API vs. Bituach Leumi's SharePoint HTML forced
  two different collectors and a `#mainContent`-only extraction to kill navigation boilerplate.
* **Fair, document-level evaluation** — chunking means one document yields many passages, so I
  collapse chunk hits to their parent `doc_id` before scoring, otherwise Recall@k is inflated.

## What I learned and what surprised me
* How much a *fair baseline* matters: a few dozen stopwords changed the entire narrative.
* That **hybrid fusion (RRF / weighted)** is a cheap, robust way to get the best of lexical
  precision and semantic recall — it consistently led on MRR/nDCG in my runs.
* I was surprised how cleanly the **MediaWiki API** exposes structured text — and how a quiet
  default (`exlimit=1`) can corrupt a dataset with no error at all. I now sanity-check dataset
  sizes as a habit.

## What I would improve
* A Hebrew lemmatizer/morphological analyzer (e.g. via a Hebrew NLP toolkit) to give the
  lexical models a fairer shot and reduce sparsity.
* A larger, multi-annotator evaluation set with graded relevance for proper nDCG.
* Compare AlephBERT against a retrieval-tuned multilingual model (e.g. E5) to separate
  "Hebrew-specific" from "retrieval-tuned" effects.

## Team contribution / work log (solo)
| Phase | Work | Notes |
|-------|------|-------|
| Design | Research question, sources, track choice, eval design | — |
| Data | API + HTML collectors, cleaning, chunking | fixed the `exlimit` bug |
| Modeling | TF-IDF, BM25, AlephBERT, hybrid fusion | shared interface |
| Evaluation | metrics, error analysis, figures | metrics implemented from formulas |
| Writing | report, slides, notebook, ethics/data/AI docs | — |

*(Mini-defense note: I can explain every metric, every design choice, and walk through any
failure case in `results/error_analysis.md`.)*
