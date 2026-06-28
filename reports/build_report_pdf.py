"""Render reports/report.md -> reports/report.html (then convert to PDF via LibreOffice)."""
import os
import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
md_text = open(os.path.join(HERE, "report.md"), encoding="utf-8").read()

# python-markdown needs a blank line before a list; insert one when a "* "/"- "
# bullet directly follows a non-blank, non-bullet line (e.g. an intro ending in ":").
_lines, _fixed = md_text.split("\n"), []
for i, ln in enumerate(_lines):
    if i and ln.lstrip().startswith(("* ", "- ")):
        prev = _fixed[-1].lstrip() if _fixed else ""
        if prev and not prev.startswith(("* ", "- ", "|")):
            _fixed.append("")
    _fixed.append(ln)
md_text = "\n".join(_fixed)

body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "sane_lists"])

CSS = """
@page { size: A4; margin: 1.5cm; }
* { box-sizing: border-box; }
body { font-family: 'Calibri','Helvetica',sans-serif; font-size: 10.2pt; line-height: 1.35;
       color: #153139; max-width: 100%; }
h1 { font-size: 19pt; color: #0B3B45; margin: 0 0 2pt; }
h2 { font-size: 13pt; color: #0E8A8F; margin: 11pt 0 3pt; border: none; }
h3 { font-size: 11pt; color: #0B3B45; margin: 8pt 0 2pt; }
p { margin: 4pt 0; }
ul { margin: 3pt 0; padding-right: 16pt; }
li { margin: 1pt 0; }
table { border-collapse: collapse; width: 100%; font-size: 9pt; margin: 5pt 0; }
th { background: #0B3B45; color: #fff; padding: 3pt 5pt; text-align: center; }
td { border: 1px solid #cfe0e0; padding: 2.5pt 5pt; text-align: center; }
td:first-child, th:first-child { text-align: left; }
code { font-family: 'Consolas',monospace; font-size: 8.6pt; background: #eef5f5; padding: 0 2pt; }
strong { color: #0B3B45; }
hr { border: none; border-top: 1px solid #cfe0e0; margin: 6pt 0; }
blockquote { color:#5C6B72; font-style: italic; border-right: 2px solid #5FBDB6; margin: 4pt 0; padding: 0 8pt 0 0; }
"""
html = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"
out = os.path.join(HERE, "report.html")
open(out, "w", encoding="utf-8").write(html)
print("wrote", out)
