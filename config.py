"""
Central configuration for the Hebrew Semantic Rights Retrieval project.

All paths are resolved relative to this file so the pipeline works identically
whether run locally (`python src/run_all.py`) or from a cloned repo in Colab.
"""
from __future__ import annotations

import os

# Force the PyTorch backend for HuggingFace. Without this, `transformers` tries to
# import TensorFlow and fails when Keras 3 (incompatible) is installed. Set before
# any transformers/sentence-transformers import (config is imported first everywhere).
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_FLAX", "0")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
RESULTS_DIR = os.path.join(ROOT, "results")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")

CORPUS_PATH = os.path.join(PROCESSED_DIR, "corpus.jsonl")
EVAL_PATH = os.path.join(PROCESSED_DIR, "eval_set.json")
EMBEDDINGS_PATH = os.path.join(PROCESSED_DIR, "emb_alephbert.npy")
EMBEDDINGS_IDS_PATH = os.path.join(PROCESSED_DIR, "emb_alephbert_ids.json")
METRICS_PATH = os.path.join(RESULTS_DIR, "metrics.csv")
PERQUERY_PATH = os.path.join(RESULTS_DIR, "per_query.csv")
ERROR_ANALYSIS_PATH = os.path.join(RESULTS_DIR, "error_analysis.md")

for _d in (RAW_DIR, PROCESSED_DIR, RESULTS_DIR, FIGURES_DIR):
    os.makedirs(_d, exist_ok=True)

# -----------------------------------------------------------------------------
# Data collection
# -----------------------------------------------------------------------------
USER_AGENT = (
    "HIT-NLP-AcademicProject/1.0 (M.Sc. course project; contact: yanikg) "
    "python-requests"
)
REQUEST_DELAY_SEC = 0.5  # politeness rate-limit between requests

KOLZCHUT_API = "https://www.kolzchut.org.il/w/api.php"

# Kol-Zchut categories (life-domains) to crawl. Each maps to a short domain tag.
# Category names are the real Hebrew category titles (verified via the API's
# list=allcategories) that exist and contain enough member pages.
KOLZCHUT_CATEGORIES = {
    "נכות": "disability",
    "אבטלה": "unemployment",
    "בריאות ומחלות": "health",
    "ילדים ונוער": "family",
    "הבטחת הכנסה": "welfare",
    "הורים": "parenting",
}
KOLZCHUT_MAX_PAGES_PER_CATEGORY = 60

# A curated set of key Bituach Leumi (National Insurance) benefit pages.
# (Title, URL, domain). Kept short and hand-picked for relevance + robustness.
BTL_PAGES = [
    ("דמי לידה", "https://www.btl.gov.il/benefits/maternity/Pages/default.aspx", "parenting"),
    ("קצבת ילדים", "https://www.btl.gov.il/benefits/children/Pages/default.aspx", "parenting"),
    ("קצבת נכות כללית", "https://www.btl.gov.il/benefits/Disability/Pages/default.aspx", "disability"),
    ("דמי אבטלה", "https://www.btl.gov.il/benefits/Unemployment/Pages/default.aspx", "unemployment"),
    ("קצבת זקנה", "https://www.btl.gov.il/benefits/old_age/Pages/default.aspx", "elderly"),
    ("הבטחת הכנסה", "https://www.btl.gov.il/benefits/Income_support/Pages/default.aspx", "welfare"),
]

# -----------------------------------------------------------------------------
# Preprocessing / chunking
# -----------------------------------------------------------------------------
CHUNK_MAX_CHARS = 600     # target max characters per passage chunk
CHUNK_MIN_CHARS = 80      # drop tiny fragments below this length

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
SEMANTIC_MODEL_NAME = "imvladikon/sentence-transformers-alephbert"

# -----------------------------------------------------------------------------
# Evaluation
# -----------------------------------------------------------------------------
K_VALUES = [1, 3, 5, 10]
RANDOM_SEED = 42

# Hybrid fusion
RRF_K = 60                # standard RRF constant
HYBRID_ALPHA = 0.5        # weight for semantic in weighted score-fusion variant
