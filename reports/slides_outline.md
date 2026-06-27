# Slides Outline — Hebrew Semantic Rights Retrieval
*Target: 20–40 slides, 20–30 min presentation. The final slide MUST be "AI Usage Disclosure".*

1. **Title** — project name (HE+EN), author, track, course, date.
2. **The problem** — citizens ask in everyday Hebrew; official info is formal/legal. Show two
   real examples side by side (*"מה מגיע לי אחרי לידה?"* vs a page title).
3. **Why it matters** — rights go unclaimed when people can't find the info. Pro-social goal.
4. **Research question & hypotheses** — semantic vs lexical; does hybrid win? H1/H2.
5. **Track & scope** — Track 3, full data-driven pipeline (one diagram of the pipeline).
6. **Data sources** — Kol-Zchut (MediaWiki API, CC-BY-SA) + Bituach Leumi (curated, robots-aware).
7. **Collection** — API vs HTML; politeness (User-Agent, rate-limit, cache); the `exlimit` bug story.
8. **Preprocessing** — niqqud stripping, boilerplate removal, chunking; corpus stats (≈296 docs / ≈1,602 chunks).
9. **Domain distribution** — bar/pie of chunks per life-domain.
10. **Evaluation set** — 40 colloquial questions, ground truth, `phrasing_gap` tag; document-level scoring.
11. **Models overview** — the 5 retrievers in one table.
12. **TF-IDF / BM25** — how lexical ranking works; the stopword fix (fair baseline).
13. **Semantic — AlephBERT** — sentence embeddings, cosine; why a Hebrew model; embedding cache.
14. **Hybrid** — Reciprocal Rank Fusion + weighted fusion (one formula each).
15. **Metrics** — Recall@k, MRR, nDCG, MAP — what each captures and why chosen.
16. **Live demo** — type a query; show TF-IDF vs semantic vs hybrid top-3.
17. **Results — table** — `metrics.csv` (`results/figures/metrics_bar.png`).
18. **Results — Recall@k curve** — `recall_curve.png`.
19. **Results — by phrasing-gap** — semantic advantage grows with the gap (H1).
20. **Win/loss heatmap** — `winloss_heatmap.png`: where each model wins per query.
21. **Embedding space** — `embedding_tsne.png`: domains cluster.
22. **Error analysis A** — semantic wins (synonymy / colloquial→formal), 1–2 cases.
23. **Error analysis B** — lexical wins (rare exact term), 1 case.
24. **Error analysis C** — both fail; what it reveals about coverage.
25. **Limitations** — small eval set, six domains, morphology, model bias.
26. **Ethics** — public/licensed data, no PII, "not legal advice" framing, source links.
27. **Reflection** — top failure (the `exlimit` silent truncation) and the fix.
28. **What I'd improve** — lemmatization, larger graded eval set, E5 baseline.
29. **Conclusion** — hybrid is the practical recommendation; contribution to Hebrew IR.
30. **AI Usage Disclosure** — Tool / Task / Extent / Human edits / Verification table.
