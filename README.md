# Geospatial Research Radar

A JupyterLite-friendly morning literature radar for geospatial data science, GIScience, public-health GIS, spatial epidemiology, GeoAI, geoprivacy, population mapping, Earth observation, and reproducible Python methods.

## What it does

- Searches **OpenAlex** and **Semantic Scholar** for recent work across configurable topic families.
- Adds an **author watchlist** (starter names: Frank Tanser, Andrew/Andy Tatem, Qiusheng Wu, Diego F. Cuadros).
- Optionally ingests `web_hits.json` from a sanctioned web-search/index provider for public posts and pages that scholarly APIs miss.
- Deduplicates by DOI/title.
- Suppresses previously seen items with `seen_items.json`.
- Gives every item three transparent scores:
  - **Interest (0-100)**: match to your research profile, watched authors, recency, open access.
  - **MVP (0-100)**: open-data availability, code/Python/Jupyter signals, concrete method, compute feasibility.
  - **Priority**: 58% Interest + 42% MVP.
- Generates a one-page clickable **PDF** and a Unicode **HTML** brief.

## Notebook order

1. `00_profile_and_queries.ipynb` - edit interests, people, thresholds, API keys, and search families.
2. `01_morning_scan.ipynb` - collect, deduplicate, score, and save the morning results.
3. `02_one_page_report.ipynb` - create `geospatial_radar_YYYY-MM-DD.pdf` and `.html`.
4. `03_web_index_bridge.ipynb` - optional bridge for indexed LinkedIn/ResearchGate/web results.

Supporting code lives in `radar_core.py`. It uses only the Python standard library plus Pyodide's browser HTTP layer when running in JupyterLite.

## JupyterLite setup

Upload this folder's notebooks, `radar_core.py`, and `radar_config.json` to a JupyterLite site that uses the Pyodide kernel. Keep all files in the same directory. Run notebook 00 once, then 01 and 02 each morning.

The notebooks write files into JupyterLite's browser-backed filesystem. If your deployment exposes kernel/file-browser synchronization, the generated JSON, CSV, HTML, PDF, and seen-state files will appear in the file browser.

## API keys

Both primary sources can be tried without a key. For sustained use, add keys in `radar_config.json`:

```json
"api_keys": {
  "openalex": "YOUR_KEY_OR_BLANK",
  "semantic_scholar": "YOUR_KEY_OR_BLANK"
}
```

Do not commit private keys to a public Git repository.

## Why LinkedIn and Google Scholar are not scraped

This project intentionally does not automate a logged-in LinkedIn session or scrape Google Scholar. Instead:

- scholarly discovery comes from open APIs;
- public web/social discovery can arrive through an external, sanctioned search/index provider as `web_hits.json`;
- Google Scholar alerts can remain a separate human-readable backup channel.

This makes the radar much less brittle and avoids tying the project to unauthorized browser automation.

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

## Moving from "morning scan" to "innovation catalyst"

When an item scores highly, use the automatically generated `MVP:` line as the starting hypothesis for a separate prototype notebook. A useful pattern is:

1. State the transferable method in one sentence.
2. Choose one tiny public or synthetic dataset.
3. Implement a baseline and the new method.
4. Compare one or two quantitative diagnostics plus one map/plot.
5. End with "what would make this production-worthy?" and links to the source paper/code.

That structure makes the prototype shareable even when the full paper uses data or compute you cannot reproduce exactly.

## Fully unattended mornings (Phase 2)

JupyterLite runs in the browser, so it is best for the interactive review/prototyping layer. For unattended daily collection, use the included `run_radar.py` from ordinary Python in GitHub Actions, cron, or a cloud function. The same core code then writes the dated report automatically. A separate web-index job can populate `web_hits.json` before the radar runs.

No schedule is hard-coded in this starter kit; choose the morning time and timezone that fit your routine.
