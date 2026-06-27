"""
End-to-end pipeline orchestrator.

    python src/run_all.py [--force-scrape] [--allow-offline]

Steps:
  1. Build (or load) the corpus from Kol-Zchut + Bituach Leumi.
  2. Build all retrievers (TF-IDF, BM25, AlephBERT semantic, Hybrid RRF + weighted).
  3. Evaluate -> results/metrics.csv, results/per_query.csv.
  4. Error analysis -> results/error_analysis.md.
  5. Visualizations -> results/figures/*.png.

Flags:
  --force-scrape   re-download the source pages (ignores the raw cache).
  --allow-offline  if the semantic model can't be downloaded (e.g. HuggingFace is
                   firewalled), fall back to an offline stand-in encoder so the
                   pipeline still runs for verification. NOT for real results.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_corpus  # noqa: E402
import config  # noqa: E402
import error_analysis  # noqa: E402
import evaluate  # noqa: E402
import retrievers as R  # noqa: E402
import visualize  # noqa: E402


def main(argv):
    force_scrape = "--force-scrape" in argv
    allow_offline = "--allow-offline" in argv

    print("=" * 70)
    print("STEP 1/5  Build corpus")
    if force_scrape or not os.path.exists(config.CORPUS_PATH):
        build_corpus.build(force_scrape=force_scrape)
    corpus = build_corpus.load_corpus()
    print(f"  corpus: {len(corpus)} chunks, {len({r['doc_id'] for r in corpus})} docs")

    print("=" * 70)
    print("STEP 2/5  Build retrievers")
    retrievers = R.build_all(corpus, include_bm25=True, offline_fallback=allow_offline)
    print(f"  retrievers: {', '.join(retrievers)}")

    print("=" * 70)
    print("STEP 3/5  Evaluate")
    metrics_df, per_query_df = evaluate.run(retrievers)

    print("=" * 70)
    print("STEP 4/5  Error analysis")
    error_analysis.build(retrievers, corpus)

    print("=" * 70)
    print("STEP 5/5  Visualizations")
    embeddings = getattr(retrievers["semantic"], "embeddings", None)
    visualize.run(metrics_df, per_query_df, corpus, embeddings)

    print("=" * 70)
    print("DONE. Artifacts:")
    for p in (config.METRICS_PATH, config.PERQUERY_PATH, config.ERROR_ANALYSIS_PATH):
        print("  -", os.path.relpath(p, config.ROOT))
    print("  -", os.path.relpath(config.FIGURES_DIR, config.ROOT) + "/*.png")
    print("\nResults table:\n")
    print(metrics_df.to_string())


if __name__ == "__main__":
    main(sys.argv[1:])
