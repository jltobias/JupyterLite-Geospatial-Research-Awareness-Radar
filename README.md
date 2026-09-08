# Geospatial Research Radar

A JupyterLite-based morning literature radar for geospatial data science, GIScience, public-health GIS, spatial epidemiology, GeoAI, geoprivacy, population mapping, Earth observation, and reproducible Python methods.

## Launch the live JupyterLite site

**Live JupyterLite index:** https://jltobias.github.io/JupyterLite-Geospatial-Research-Awareness-Radar/index.html

After the first successful GitHub Pages deployment, that URL opens the browser-only JupyterLite environment. The Python kernel runs through Pyodide, so no local Python installation is required.

For the normal morning workflow, open the live site and run the notebooks in this order:

1. `00_profile_and_queries.ipynb` - edit interests, people, thresholds, API keys, and search families.
2. `01_morning_scan.ipynb` - collect, deduplicate, score, and save the morning results.
3. `02_one_page_report.ipynb` - create `geospatial_radar_YYYY-MM-DD.pdf` and `.html`.
4. `03_web_index_bridge.ipynb` - optional bridge for indexed LinkedIn/ResearchGate/public-web results.

## What it does

- Searches **OpenAlex** and **Semantic Scholar** for recent work across configurable topic families.
- Adds an **author watchlist** (starter names: Frank Tanser, Andrew/Andy Tatem, Qiusheng Wu, Diego F. Cuadros).
- Optionally ingests `web_hits.json` from a sanctioned web-search/index provider for public posts and pages that scholarly APIs miss.
- Deduplicates by DOI/title.
- Suppresses previously seen items with `seen_items.json`.
- Gives every item three transparent scores:
  - **Interest (0-100):** match to your research profile, watched authors, recency, and open-access signals.
  - **MVP (0-100):** open-data availability, code/Python/Jupyter signals, concrete method, and compute feasibility.
  - **Priority:** 58% Interest + 42% MVP.
- Generates a one-page clickable **PDF** and a Unicode **HTML** brief.

Supporting code lives in `radar_core.py`. The browser workflow uses the Python standard library plus Pyodide's browser HTTP layer, so the radar does not depend on compiled geospatial packages merely to perform discovery, scoring, or report generation.

## JupyterLite / GitHub Pages deployment

This repository now contains a GitHub Actions workflow that builds the site with `jupyterlite-core` and the Pyodide kernel, validates the notebooks and Python source, verifies that `dist/index.html` was generated, and deploys `dist/` to GitHub Pages.

The workflow is in:

```text
.github/workflows/jupyterlite.yml
```

Build dependencies are defined in:

```text
requirements.txt
```

The deployment runs automatically when `main` changes, and it can also be started manually from the GitHub **Actions** tab.

### One-time GitHub Pages setting

If GitHub Pages has not previously been enabled for this repository, open:

**Repository Settings -> Pages -> Build and deployment -> Source -> GitHub Actions**

Once the workflow completes successfully, the live site should be available at:

https://jltobias.github.io/JupyterLite-Geospatial-Research-Awareness-Radar/index.html

## Why this works in JupyterLite

The notebooks use the `Python (Pyodide)` kernel. In `radar_core.py`, HTTP requests detect the browser/Pyodide runtime and use `pyodide.http.pyfetch`; ordinary CPython uses `urllib.request`. PDF generation is implemented directly with the Python standard library rather than relying on ReportLab or another native dependency.

A browser-only deployment still has one important constraint: remote scholarly APIs must permit cross-origin browser requests. The scan is designed to continue if an individual source is blocked or rate-limited and records source-specific errors rather than failing the entire run.

Files created by the notebooks live in JupyterLite's browser-backed filesystem. That includes dated JSON/CSV results, `seen_items.json`, HTML reports, and PDF reports. Browser storage is local to the browser/profile unless you explicitly export or synchronize files elsewhere.

## API keys

Both primary sources can be tried without a key. For sustained use, add keys in `radar_config.json`:

```json
"api_keys": {
  "openalex": "YOUR_KEY_OR_BLANK",
  "semantic_scholar": "YOUR_KEY_OR_BLANK"
}
```

Do not commit private keys to this public repository. For a purely browser-based public deployment, avoid putting private API keys into notebooks or committed configuration because site visitors can inspect browser-delivered content.

## Why LinkedIn and Google Scholar are not scraped

This project intentionally does not automate a logged-in LinkedIn session or scrape Google Scholar. Instead:

- scholarly discovery comes from open APIs;
- public web/social discovery can arrive through an external, sanctioned search/index provider as `web_hits.json`;
- Google Scholar alerts can remain a separate human-readable backup channel.

This makes the radar less brittle and avoids tying the project to unauthorized browser automation.

## `web_hits.json` format

Notebook 01 automatically merges this file when present:

```json
[
  {
    "title": "Post or publication title",
    "url": "https://example.org/item",
    "snippet": "Short indexed snippet describing the method or release.",
    "date": "2026-09-04",
    "author": "Researcher Name",
    "source": "Web index",
    "open_access": true
  }
]
```

Notebook 03 generates `web_search_queries.json` containing search strings for watched people and ResearchGate/publication pages.

## Scoring philosophy

The score is intentionally interpretable and easy to tune. It is not intended to claim scientific quality. The **MVP score asks a different question**: "Can I reproduce or adapt the core idea quickly with open/synthetic data and lightweight Python?"

High MVP scores tend to have several of these signals:

- public/open data or familiar open data products;
- source code, Python package, GitHub repository, notebook, API, or explicit algorithm;
- a method that can be isolated from the full research pipeline;
- an open-access paper or direct PDF;
- modest compute requirements, or a credible small-data surrogate.

Large-model/GPU/HPC terms reduce JupyterLite feasibility, but strong implementation signals can partially offset that penalty because a low-fidelity surrogate may still be worthwhile.

## Moving from morning scan to innovation catalyst

When an item scores highly, use the automatically generated `MVP:` line as the starting hypothesis for a separate prototype notebook. A useful pattern is:

1. State the transferable method in one sentence.
2. Choose one tiny public or synthetic dataset.
3. Implement a baseline and the new method.
4. Compare one or two quantitative diagnostics plus one map/plot.
5. End with "what would make this production-worthy?" and links to the source paper/code.

That structure makes the prototype shareable even when the full paper uses data or compute you cannot reproduce exactly.

## Fully unattended mornings

JupyterLite runs in the browser, so it is best for the interactive review/prototyping layer. For unattended daily collection, use the included `run_radar.py` from ordinary Python in GitHub Actions, cron, or a cloud function. The same core code can write the dated report automatically. A separate web-index job can populate `web_hits.json` before the radar runs.

No schedule is hard-coded in this repository; choose the morning time and timezone that fit your routine.
