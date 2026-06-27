# AI Usage Disclosure

AI tools were used **only as support tools**. Every line of submitted code was read,
understood, executed, and verified by the author, who can explain all of it.

## Format: Tool / Task / Extent / Human edits / Verification

| Tool | Task | Extent | Human edits / what was rewritten | Verification |
|------|------|--------|----------------------------------|--------------|
| **Claude (Anthropic)** | Project scaffolding, docstrings, and debugging assistance | Moderate | Reworked the retrieval logic and hybrid fusion; **independently diagnosed and fixed the MediaWiki `exlimit=1` bug** that silently truncated the corpus; tuned the Hebrew stopword list, chunking sizes, and the `#mainContent` selector for Bituach Leumi | Ran the full pipeline end-to-end; manually inspected the scraped corpus, the metrics table, and every figure |
| **ChatGPT** | Clarifying IR metric definitions (MRR, nDCG, MAP) | Light | Implemented all metrics from scratch in `src/evaluate.py` | Cross-checked each metric against its textbook formula on small hand-computed inputs |
| **GitHub Copilot** | Line-level autocomplete while typing | Light | Accepted only trivial completions; rejected/edited anything non-obvious | Covered by running the code and the test queries |

## What was done independently (no AI authoring)

* Choice of research question, track, sources, and the formal-vs-colloquial framing.
* Authoring the **40-question evaluation set** and mapping each to its ground-truth document.
* Selecting the six Kol-Zchut life-domains and curating the Bituach Leumi page list.
* All design decisions: chunk granularity, document-level scoring, RRF vs weighted fusion.

## What was independently verified

* Corpus integrity — every ground-truth `doc_id` in the eval set exists in the corpus (checked programmatically).
* Metric correctness — verified on toy rankings before trusting the aggregate numbers.
* Results — figures and the metrics table were regenerated and inspected, not taken on trust.

Undisclosed AI usage would constitute academic misconduct. This disclosure also appears in
the report, the notebook's first cell, and the final slide.
