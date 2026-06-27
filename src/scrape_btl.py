"""
Collect a small, curated set of benefit pages from Bituach Leumi (המוסד לביטוח לאומי).

Unlike Kol-Zchut, btl.gov.il is a SharePoint site with no clean API, so we scrape
HTML. We:
  * check robots.txt first (urllib.robotparser) and skip disallowed URLs,
  * send a descriptive User-Agent and rate-limit between requests,
  * extract only the main content container (#mainContent) to avoid menu/nav boilerplate,
  * strip residual UI strings ("הדפס", "שלח לחבר", "שתף", ...).

This is intentionally a *supplementary* source (~10 hand-picked pages): it adds the
official-register phrasing that contrasts with Kol-Zchut's explanatory style, which is
exactly the formal-vs-colloquial gap the project studies.

Each raw record: {"source","page_id","title","url","domain","text"}
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.robotparser as robotparser

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402

RAW_PATH = os.path.join(config.RAW_DIR, "btl.json")
ROBOTS_URL = "https://www.btl.gov.il/robots.txt"

# UI / boilerplate lines to drop after extraction.
BOILERPLATE = {
    "הדפס", "שלח לחבר", "שתף", "דלג לתוכן ראשי", "חזרה למעלה",
    "הפעל מצב נגיש יותר", "בטל מצב נגיש יותר",
}


def _robots():
    rp = robotparser.RobotFileParser()
    rp.set_url(ROBOTS_URL)
    try:
        rp.read()
    except Exception as e:  # pragma: no cover - network hiccup
        print(f"[btl] could not read robots.txt ({e}); proceeding conservatively")
    return rp


def _clean(text: str) -> str:
    lines = []
    for ln in text.split("\n"):
        ln = ln.strip()
        if not ln or ln in BOILERPLATE:
            continue
        lines.append(ln)
    return "\n".join(lines)


def fetch_page(session, url):
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    main = soup.find(id="mainContent") or soup.body
    if main is None:
        return ""
    for tag in main(["script", "style"]):
        tag.decompose()
    return _clean(main.get_text("\n", strip=True))


def scrape(force=False):
    if os.path.exists(RAW_PATH) and not force:
        with open(RAW_PATH, encoding="utf-8") as f:
            cached = json.load(f)
        print(f"[btl] using cached {len(cached)} pages ({RAW_PATH})")
        return cached

    session = requests.Session()
    session.headers.update({"User-Agent": config.USER_AGENT})
    rp = _robots()

    records = []
    for i, (title, url, domain) in enumerate(config.BTL_PAGES):
        if not rp.can_fetch(config.USER_AGENT, url) and not rp.can_fetch("*", url):
            print(f"[btl] robots.txt disallows {url} — skipping")
            continue
        try:
            text = fetch_page(session, url)
        except Exception as e:
            print(f"[btl] failed {url}: {e}")
            continue
        if len(text) < config.CHUNK_MIN_CHARS:
            print(f"[btl] too little content at {url} (len={len(text)}) — skipping")
            continue
        records.append(
            {
                "source": "btl",
                "page_id": f"btl_{i}",
                "title": title,
                "url": url,
                "domain": domain,
                "text": text,
            }
        )
        print(f"[btl] fetched '{title}' ({len(text)} chars)")
        time.sleep(config.REQUEST_DELAY_SEC)

    with open(RAW_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"[btl] saved {len(records)} pages -> {RAW_PATH}")
    return records


if __name__ == "__main__":
    scrape(force="--force" in sys.argv)
