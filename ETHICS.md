# ETHICS.md — Ethical and Responsible NLP Statement

## Data source transparency
All data comes from two clearly identified, public sources: **Kol-Zchut** (CC-BY-SA) and the
**National Insurance Institute / Bituach Leumi** (official public-sector information). Every
corpus record keeps its `source` and canonical `url`, so any passage can be traced back to its
origin. Collection methods are documented in `DATA.md`.

## Privacy
The corpus contains **no personal data**. The sources are general informational pages about
rights and benefits — they describe eligibility rules and procedures, not individuals. The
evaluation questions are synthetic, author-written, and contain no real personal details.
No user data is collected, and the system stores no queries.

## Consent / public availability
No social-media or user-generated content is used, so there are no individual-consent concerns.
Kol-Zchut explicitly licenses its content for reuse (CC-BY-SA); Bituach Leumi pages are public
government information, fetched only from `robots.txt`-permitted URLs, rate-limited, with an
identifying User-Agent.

## Licensing / copyright and permitted use
* **Kol-Zchut:** CC-BY-SA 3.0 — reuse permitted with attribution and share-alike. Attribution
  is preserved via the stored `url`/`title`; this project is non-commercial academic work.
* **Bituach Leumi:** public official information; used in a small, curated, transformed
  (chunked) form for research, with respect for the site's `robots.txt`.
* Redistribution note: the cached corpus is included for reproducibility under the same
  attribution/share-alike terms; it is not presented as original content.

## Bias in data and model limitations
* **Domain & coverage bias.** Six life-domains are sampled (≈60 pages/category); rights not in
  these categories are absent. Results generalize only to the covered domains.
* **Source-style bias.** Kol-Zchut is explanatory; Bituach Leumi is formal-administrative.
  A model can appear better simply by matching one style.
* **Hebrew morphology.** Rich inflection and prefixed particles (ב/ל/מ/ה/ש) hurt the lexical
  baselines; the semantic model depends on AlephBERT's pre-training coverage and may encode its
  own social biases (gender, sector) learned from web text.
* **Small evaluation set.** 40 questions give indicative, not statistically tight, estimates;
  ground-truth labels reflect one annotator's judgment.

## Potential harmful applications
A rights-retrieval system could be **mistaken for legal advice**. Wrong or stale results could
cause someone to miss an entitlement or a deadline. Mitigations / intended framing:
* This is a **research prototype, not a legal or official tool**, and must not be relied on for
  decisions. Any real deployment must show the **source link** and a clear disclaimer, and defer
  to the official authority.
* The system **retrieves existing public pages** rather than generating advice, which keeps
  answers grounded and auditable and avoids fabrication.
* Eligibility rules change; a real system would need a refresh/validity process.

## Responsible-use summary
The project aims at a **pro-social goal** — making public-benefit information easier to find for
people who phrase questions in everyday language. It uses only public, appropriately licensed
data, collects no personal information, and is transparent about its limits.
