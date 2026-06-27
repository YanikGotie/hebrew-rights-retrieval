"""
Hebrew text preprocessing and chunking utilities.

Two distinct kinds of "cleaning" live here:

1. `normalize_for_index(text)` — aggressive normalization used ONLY to build the
   TF-IDF / BM25 token stream: strips niqqud (vowel points) and cantillation,
   removes punctuation, and collapses whitespace. We deliberately keep Hebrew
   final-form letters as-is (folding them changed nothing measurable and risks
   merging unrelated tokens); the main lexical gain comes from niqqud removal.

2. `clean_passage(text)` — light cleaning that preserves readable Hebrew for the
   semantic encoder and for display in error analysis (keeps punctuation, drops
   wiki artifacts and empty section headers).

`chunk_document(...)` splits a page into passage-sized chunks on paragraph
boundaries (≤ CHUNK_MAX_CHARS), which is the retrieval unit.
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402

# A compact list of high-frequency Hebrew function words (pronouns, prepositions,
# question words, auxiliaries). Removing them gives the lexical baselines a fair
# chance: short colloquial queries are otherwise dominated by these tokens.
HEB_STOPWORDS = [
    "של", "את", "על", "מה", "לי", "לך", "לו", "לה", "אני", "אתה", "הוא", "היא",
    "הם", "הן", "אנחנו", "אתם", "זה", "זו", "זאת", "אלה", "גם", "כי", "אם", "או",
    "עם", "לא", "כן", "יש", "אין", "מי", "איך", "כמה", "אבל", "רק", "כל", "אל",
    "עד", "אחרי", "לפני", "בין", "אצל", "הזה", "הזאת", "וגם", "וכן", "אשר", "כדי",
    "בגלל", "למה", "מתי", "איפה", "להם", "להן", "שלי", "שלך", "שלו", "שלה", "שלנו",
    "שלהם", "וכו", "יותר", "פחות", "מאוד", "הרבה", "מעט", "כבר", "עוד", "שוב",
    "פעם", "היה", "היתה", "להיות", "מתוך", "תוך", "כמו", "לפי", "אותו", "אותה",
    "אותי", "אותך", "אותם", "הללו", "כך", "ככה", "אז", "כעת", "עכשיו", "צריך",
    "צריכה", "רוצה", "יכול", "יכולה", "מגיע", "ואת",
]

# Unicode ranges: Hebrew points (niqqud) U+0591–U+05C7, plus marks.
_NIQQUD = re.compile(r"[֑-ׇ]")
_NON_HEB_WORD = re.compile(r"[^א-ת0-9a-zA-Z]+")
_MULTISPACE = re.compile(r"[ \t]+")
_MULTINEWLINE = re.compile(r"\n{3,}")
# MediaWiki section markers like "== מי זכאי? =="
_SECTION = re.compile(r"^=+\s*(.*?)\s*=+$", re.MULTILINE)


def strip_niqqud(text: str) -> str:
    return _NIQQUD.sub("", text)


def normalize_for_index(text: str) -> str:
    """Normalized whitespace-joined token stream for lexical models."""
    text = strip_niqqud(text)
    text = _NON_HEB_WORD.sub(" ", text)
    return _MULTISPACE.sub(" ", text).strip().lower()


def clean_passage(text: str) -> str:
    """Light cleaning that keeps readable Hebrew for the encoder / display."""
    text = strip_niqqud(text)
    # Turn "== Heading ==" into a plain heading line.
    text = _SECTION.sub(lambda m: m.group(1), text)
    text = text.replace("‏", "").replace("‎", "")  # bidi marks
    text = _MULTISPACE.sub(" ", text)
    text = _MULTINEWLINE.sub("\n\n", text)
    return text.strip()


def _split_paragraphs(text: str):
    parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if p.strip()]


def chunk_document(text, max_chars=None, min_chars=None):
    """Split a page into passage chunks on paragraph boundaries.

    Paragraphs are greedily packed up to `max_chars`. An over-long paragraph is
    hard-split on sentence-ish boundaries so no chunk exceeds the cap.
    """
    max_chars = max_chars or config.CHUNK_MAX_CHARS
    min_chars = min_chars or config.CHUNK_MIN_CHARS

    chunks, buf = [], ""
    for para in _split_paragraphs(text):
        if len(para) > max_chars:
            # flush current buffer, then hard-split the long paragraph
            if buf:
                chunks.append(buf.strip())
                buf = ""
            for piece in _hard_split(para, max_chars):
                chunks.append(piece.strip())
            continue
        if len(buf) + len(para) + 1 <= max_chars:
            buf = f"{buf}\n{para}" if buf else para
        else:
            if buf:
                chunks.append(buf.strip())
            buf = para
    if buf:
        chunks.append(buf.strip())

    return [c for c in chunks if len(c) >= min_chars]


def _hard_split(para, max_chars):
    sentences = re.split(r"(?<=[.!?。])\s+", para)
    out, buf = [], ""
    for s in sentences:
        if len(s) > max_chars:  # extreme case: chop by characters
            for j in range(0, len(s), max_chars):
                out.append(s[j : j + max_chars])
            continue
        if len(buf) + len(s) + 1 <= max_chars:
            buf = f"{buf} {s}" if buf else s
        else:
            if buf:
                out.append(buf)
            buf = s
    if buf:
        out.append(buf)
    return out
