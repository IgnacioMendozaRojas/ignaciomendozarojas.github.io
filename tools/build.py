"""Copy figures from the project repositories, fill the figures in index.html from their
results.json, and render the SQM reports as pages.

Run from the site root with the project repositories checked out next to it:
    python tools/build.py
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import markdown

SITE = Path(__file__).resolve().parents[1]
REPOS = SITE.parent

FIGURES = {
    "ccr": "counterparty-credit-risk/docs/margin-period-{theme}.png",
    "liquidity": "chile-bank-liquidity/docs/figures/cost-{theme}.png",
    "clinics": "chile-clinics-benchmark/docs/figures/allowance_coverage-{theme}.png",
    "sqm": "equity-research-engine/companies/sqm/reports/figures/montecarlo-2026-10-16-{theme}.png",
    "restaurant": "restaurant-analytics/docs/break-even-{theme}.png",
    "governance": "ownership-and-boards/docs/figures/representation-{theme}.png",
}
# figures in index.html sit between <!--x:repo.key--> and <!--/x--> and come from the
# "facts" of each repository's results.json, so the page never drifts from the repo
RESULTS = {"liquidity": "chile-bank-liquidity/results.json"}
MARK = re.compile(r"<!--x:([a-z]+)\.([a-z0-9_]+)-->(.*?)<!--/x-->", re.DOTALL)
REPORTS = REPOS / "equity-research-engine/companies/sqm/reports"
TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../../assets/style.css">
</head>
<body>
<main class="page report">
<p class="back"><a href="../../index.html">Ignacio Mendoza Rojas</a> · <a href="https://github.com/IgnacioMendozaRojas/equity-research-engine">Code for this report</a></p>
{body}
</main>
</body>
</html>
"""


def figures() -> None:
    out = SITE / "assets/fig"
    out.mkdir(parents=True, exist_ok=True)
    for name, src in FIGURES.items():
        for theme in ("light", "dark"):
            shutil.copy(REPOS / src.format(theme=theme), out / f"{name}-{theme}.png")


def fill(text: str, facts: dict[str, dict[str, str]]) -> str:
    """Replace each marked figure; a key missing from results.json raises."""

    def sub(mo: re.Match) -> str:
        repo, key = mo.group(1), mo.group(2)
        if key not in facts.get(repo, {}):
            raise KeyError(f"index.html marker {repo}.{key} has no value in {RESULTS.get(repo)}")
        return f"<!--x:{repo}.{key}-->{facts[repo][key]}<!--/x-->"

    return MARK.sub(sub, text)


def numbers() -> None:
    facts = {
        repo: json.loads((REPOS / path).read_text(encoding="utf-8"))["facts"] for repo, path in RESULTS.items()
    }
    page = SITE / "index.html"
    page.write_text(fill(page.read_text(encoding="utf-8"), facts), encoding="utf-8")


def reports() -> None:
    out = SITE / "research/sqm"
    (out / "figures").mkdir(parents=True, exist_ok=True)
    for md in sorted(REPORTS.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        html = markdown.markdown(text, extensions=["tables", "md_in_html"])
        html = re.sub(r"<table>", '<div class="table-wrap"><table>', html).replace("</table>", "</table></div>")
        for fig in re.findall(r'figures/([\w.-]+\.png)', html):
            shutil.copy(REPORTS / "figures" / fig, out / "figures" / fig)
        title = re.search(r"^# (.+)$", text, re.M).group(1)
        date = md.stem
        (out / f"{date}.html").write_text(
            TEMPLATE.format(
                title=f"{title}, {date}",
                description=f"SQM equity research report with valuation date {date}, built from public filings.",
                body=html,
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    figures()
    numbers()
    reports()
    print("built")
