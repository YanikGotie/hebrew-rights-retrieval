"""
Collect a Hebrew rights corpus from Kol-Zchut (כל-זכות) via the MediaWiki API.

Why the API and not HTML scraping?
  Kol-Zchut runs on MediaWiki, so the official `action=query` API gives us clean,
  section-structured plain text (`prop=extracts&explaintext=1`) plus the canonical
  URL and page id. This is far more robust and reproducible than parsing HTML, and
  the content is licensed CC-BY-SA (see DATA.md / ETHICS.md).

Pipeline:
  1. For each configured category, list its member pages (`list=categorymembers`).
  2. Fetch a plain-text extract for each page (batched, `prop=extracts`).
  3. Cache everything to data/raw/kolzchut.json (idempotent: re-running uses cache).

Each raw record:
  {"source","page_id","title","url","domain","text"}
"""
from __future__ import annotations

import json
import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402

RAW_PATH = os.path.join(config.RAW_DIR, "kolzchut.json")


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": config.USER_AGENT})
    return s


def list_category_pages(session, category, limit):
    """Return [(page_id, title)] for pages directly in a category."""
    pages, cont = [], None
    while len(pages) < limit:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"קטגוריה:{category}",
            "cmtype": "page",
            "cmlimit": min(500, limit - len(pages)),
            "format": "json",
        }
        if cont:
            params["cmcontinue"] = cont
        data = session.get(config.KOLZCHUT_API, params=params, timeout=30).json()
        for m in data.get("query", {}).get("categorymembers", []):
            pages.append((m["pageid"], m["title"]))
        cont = data.get("continue", {}).get("cmcontinue")
        if not cont:
            break
        time.sleep(config.REQUEST_DELAY_SEC)
    return pages[:limit]


def fetch_extracts(session, page_ids):
    """Fetch full plain-text extract + canonical URL for each page id.

    The TextExtracts extension only allows batching (exlimit>1) when `exintro`
    limits output to the lead section. Because we want the *full* page text for
    retrieval, we must request one page per call (exlimit is forced to 1 anyway).
    """
    out = {}
    total = len(page_ids)
    for n, pid in enumerate(page_ids, 1):
        params = {
            "action": "query",
            "prop": "extracts|info",
            "explaintext": 1,
            "exsectionformat": "plain",
            "inprop": "url",
            "pageids": str(pid),
            "format": "json",
        }
        try:
            data = session.get(config.KOLZCHUT_API, params=params, timeout=60).json()
        except Exception as e:  # pragma: no cover - network hiccup
            print(f"[kolzchut]   ! page {pid} failed: {e}")
            continue
        for p, pg in data.get("query", {}).get("pages", {}).items():
            out[int(p)] = {
                "title": pg.get("title", ""),
                "url": pg.get("fullurl", ""),
                "text": pg.get("extract", "") or "",
            }
        if n % 25 == 0:
            print(f"[kolzchut]   ...fetched {n}/{total} extracts")
        time.sleep(config.REQUEST_DELAY_SEC)
    return out


def scrape(force=False):
    if os.path.exists(RAW_PATH) and not force:
        with open(RAW_PATH, encoding="utf-8") as f:
            cached = json.load(f)
        print(f"[kolzchut] using cached {len(cached)} pages ({RAW_PATH})")
        return cached

    session = _session()
    # Collect (page_id -> domain); first category wins to avoid duplicates.
    pid_to_domain, pid_to_title = {}, {}
    for category, domain in config.KOLZCHUT_CATEGORIES.items():
        members = list_category_pages(session, category, config.KOLZCHUT_MAX_PAGES_PER_CATEGORY)
        new = 0
        for pid, title in members:
            if pid not in pid_to_domain:
                pid_to_domain[pid] = domain
                pid_to_title[pid] = title
                new += 1
        print(f"[kolzchut] category '{category}' ({domain}): {len(members)} members, {new} new")
        time.sleep(config.REQUEST_DELAY_SEC)

    page_ids = list(pid_to_domain.keys())
    print(f"[kolzchut] fetching extracts for {len(page_ids)} unique pages...")
    extracts = fetch_extracts(session, page_ids)

    records = []
    for pid in page_ids:
        ex = extracts.get(pid)
        if not ex or len(ex["text"]) < config.CHUNK_MIN_CHARS:
            continue
        records.append(
            {
                "source": "kolzchut",
                "page_id": pid,
                "title": ex["title"] or pid_to_title.get(pid, ""),
                "url": ex["url"],
                "domain": pid_to_domain[pid],
                "text": ex["text"],
            }
        )

    with open(RAW_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"[kolzchut] saved {len(records)} pages -> {RAW_PATH}")
    return records


if __name__ == "__main__":
    scrape(force="--force" in sys.argv)
