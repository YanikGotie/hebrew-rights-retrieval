# DATA.md — Dataset source, license, and reproduction

## Overview

A self-collected Hebrew corpus about **social rights, benefits, and bureaucratic procedures**,
plus a hand-authored evaluation set. No Kaggle data, notebooks, or code were used.

| Artifact | Path | Content |
|----------|------|---------|
| Raw Kol-Zchut pages | `data/raw/kolzchut.json` | API pulls: title, url, domain, full text |
| Raw Bituach Leumi pages | `data/raw/btl.json` | Scraped `#mainContent` text |
| Chunked corpus | `data/processed/corpus.jsonl` | One passage per line (see schema below) |
| Evaluation set | `data/processed/eval_set.json` | 40 questions → ground-truth `doc_id`s |

## Sources

### 1. Kol-Zchut (כל-זכות) — primary source
* Site: <https://www.kolzchut.org.il>
* **Collected via the official MediaWiki API** (`https://www.kolzchut.org.il/w/api.php`),
  not HTML scraping: `list=categorymembers` to enumerate pages per category, then
  `prop=extracts&explaintext=1` for clean section-structured plain text.
* Domains (categories) collected: `נכות` (disability), `אבטלה` (unemployment),
  `בריאות ומחלות` (health), `ילדים ונוער` (family), `הבטחת הכנסה` (income support),
  `הורים` (parenting) — capped at 60 pages each, de-duplicated by page id.
* **License:** Kol-Zchut content is published under **CC-BY-SA 3.0**
  (<https://www.kolzchut.org.il/he/כל-זכות:זכויות_יוצרים>) — free to reuse with attribution
  and share-alike, which covers academic/research use here.

### 2. Bituach Leumi / National Insurance Institute (המוסד לביטוח לאומי) — supplementary
* Site: <https://www.btl.gov.il>
* A small curated list (`config.BTL_PAGES`) of key benefit pages, scraped from the
  `#mainContent` region with `requests` + `BeautifulSoup`, navigation boilerplate removed.
* **Permitted use:** `robots.txt` (<https://www.btl.gov.il/robots.txt>) was checked
  programmatically (`urllib.robotparser`) before each fetch; only allowed URLs are fetched.
  Content is official public-sector information published for citizens.

### Politeness
* Descriptive `User-Agent` identifying the academic project (`config.USER_AGENT`).
* Rate-limit of `REQUEST_DELAY_SEC = 0.5s` between requests.
* Raw pulls are cached so re-runs do not re-hit the servers.

## Corpus schema (`corpus.jsonl`)

```json
{
  "chunk_id": "kolzchut_1521_2",
  "doc_id":   "kolzchut_1521",
  "title":    "דמי אבטלה",
  "url":      "https://www.kolzchut.org.il/he/דמי_אבטלה",
  "source":   "kolzchut",
  "domain":   "unemployment",
  "text":     "<clean passage for display / semantic encoding>",
  "text_norm":"<normalized token stream for lexical models>"
}
```
`doc_id` is the page-level id and is the granularity at which retrieval is scored.

## Evaluation set (`eval_set.json`)
40 colloquial natural-language questions, each with `relevant_doc_ids` (ground truth),
a `domain`, and a `phrasing_gap` tag (`low`/`medium`/`high`). Authored manually by reading
the candidate documents; every `doc_id` is verified to exist in the corpus.

## Train / validation / test split (`eval_split.json`)
Query-level split (this is retrieval, not row classification): the **corpus is the index**
(fit without labels); the 40 labeled queries are split **stratified by domain, seed 42** into
**dev/validation (14)** and **held-out test (26)** via `src/splits.py`. Per-split metrics:
`results/metrics_by_split.csv`. No hyper-parameters were tuned on the labeled queries, so the
split is an unbiased robustness check.

## Reproduction

```bash
pip install -r requirements.txt

# Full pipeline (scrape if needed → corpus → retrievers → eval → figures):
python src/run_all.py

# Force a fresh scrape (ignores data/raw cache):
python src/run_all.py --force-scrape

# Individual stages:
python src/build_corpus.py      # scrape + chunk -> corpus.jsonl
python src/evaluate.py          # metrics.csv + per_query.csv
python src/error_analysis.py    # error_analysis.md
python src/visualize.py         # figures/*.png
```

> **Note:** the AlephBERT semantic model is downloaded from HuggingFace on first run.
> If your network blocks HuggingFace, run the project in **Google Colab**
> (`notebooks/NLP_Project.ipynb`). `python src/run_all.py --allow-offline` runs the
> rest of the pipeline with a non-semantic stand-in for plumbing tests only.

Exact page counts depend on live category membership at scrape time (the sites are updated);
the cached `data/raw/*.json` files pin the exact snapshot used for the reported results.
