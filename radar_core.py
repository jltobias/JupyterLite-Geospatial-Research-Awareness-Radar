"""Core utilities for the Geospatial Research Radar.

Designed to run in both JupyterLite/Pyodide and ordinary CPython.
No third-party Python dependencies are required.
"""
from __future__ import annotations

import asyncio
import csv
import difflib
import html
import json
import math
import os
import re
import sys
import textwrap
import time
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import urlencode, quote

DEFAULT_CONFIG: Dict[str, Any] = {
    "profile": {
        "name": "James L. Tobias",
        "linkedin": "https://www.linkedin.com/in/jimtobias/",
        "google_scholar": "https://scholar.google.com/citations?user=ftKxo3sAAAAJ&hl=en",
        "researchgate": "https://www.researchgate.net/profile/James-Tobias-2",
        "orcid": "https://orcid.org/0000-0001-8694-5002",
    },
    "lookback_days": 4,
    "max_results_per_query": 12,
    "max_report_items": 7,
    "minimum_priority_score": 42,
    "sources": {
        "openalex": True,
        "semantic_scholar": True,
        "external_web_hits_file": "web_hits.json",
    },
    "api_keys": {
        "openalex": "",
        "semantic_scholar": "",
    },
    "watch_people": [
        "Frank Tanser",
        "Andrew J Tatem",
        "Andy Tatem",
        "Qiusheng Wu",
        "Diego F Cuadros",
        "Diego Cuadros",
    ],
    "query_families": [
        "GeoAI geospatial artificial intelligence GIS",
        "geospatial foundation model spatial explicitness",
        "spatial epidemiology disease mapping public health GIS",
        "population mapping mobility accessibility human settlement",
        "geoprivacy differential privacy spatial data",
        "spatial statistics Bayesian point process hotspot cluster",
        "remote sensing Earth observation open data STAC",
        "geospatial LLM spatial reasoning GIS agent",
        "spatiotemporal machine learning graph neural network",
        "open source Python Jupyter geospatial reproducible",
    ],
    "interest_groups": {
        "health_spatial": [
            "spatial epidemiology", "public health", "disease mapping", "health geography",
            "health geoai", "hiv", "tuberculosis", "malaria", "outbreak", "epidemic",
            "exposure", "accessibility", "health risk",
        ],
        "geoai": [
            "geoai", "geospatial artificial intelligence", "geospatial foundation",
            "foundation model", "spatial reasoning", "multimodal", "transformer",
            "representation learning", "large language model", "llm", "agent",
        ],
        "population_mobility": [
            "population mapping", "small area", "mobility", "migration", "human settlement",
            "worldpop", "travel time", "accessibility", "activity space", "movement",
        ],
        "spatial_methods": [
            "spatial statistics", "bayesian spatial", "spatiotemporal", "point process",
            "spatial scan", "hotspot", "cluster detection", "moran", "geographically weighted",
            "spatial causal", "network", "graph neural", "uncertainty", "downscal",
        ],
        "privacy_equity": [
            "geoprivacy", "differential privacy", "privacy", "confidential", "equity",
            "fairness", "responsible ai", "bias", "disclosure risk",
        ],
        "earth_observation": [
            "remote sensing", "earth observation", "landsat", "sentinel", "hls", "stac",
            "land surface temperature", "urban heat", "night light", "change detection",
        ],
        "open_reproducible": [
            "open source", "python", "jupyter", "notebook", "github", "package",
            "reproducible", "software", "open data", "workflow",
        ],
    },
    "prototype_signals": {
        "open_data": [
            "open data", "openstreetmap", "osm", "worldpop", "ghsl", "landsat", "sentinel",
            "hls", "era5", "stac", "census", "dem", "srtm", "modis", "viirs", "copernicus",
            "openalex", "geojson", "csv", "publicly available", "data availability",
        ],
        "implementation": [
            "python", "github", "code", "open source", "package", "jupyter", "notebook",
            "repository", "software", "pypi", "api", "tutorial", "workflow", "algorithm",
        ],
        "concrete_method": [
            "algorithm", "model", "framework", "method", "workflow", "pipeline", "estimator",
            "index", "metric", "test", "benchmark", "estimation", "estimator", "segmentation", "classification",
            "downscaling", "interpolation", "optimization", "clustering", "simulation",
        ],
        "browser_heavy": [
            "gpu", "cuda", "multi-gpu", "billion parameter", "large language model",
            "foundation model", "deep learning", "training from scratch", "petabyte",
            "high performance computing", "hpc",
        ],
    },
    "ignore_terms": [
        "job opening", "hiring", "webinar only", "conference registration", "advertisement",
        "sales", "marketing", "real estate listing",
    ],
}


def deep_copy_jsonable(obj: Any) -> Any:
    return json.loads(json.dumps(obj))


def save_json(obj: Any, path: str | Path) -> None:
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def load_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def today_local() -> date:
    # Browser/host local date is appropriate for a morning brief.
    return datetime.now().astimezone().date()


def parse_date(value: Any) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    s = str(value).strip()[:10]
    try:
        return date.fromisoformat(s)
    except Exception:
        return None


def normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def reconstruct_openalex_abstract(inv: Optional[Dict[str, List[int]]]) -> str:
    if not inv:
        return ""
    positions: List[Tuple[int, str]] = []
    for word, poss in inv.items():
        for pos in poss:
            positions.append((int(pos), word))
    positions.sort()
    return " ".join(word for _, word in positions)


async def fetch_json(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> Dict[str, Any]:
    """Fetch JSON in Pyodide/JupyterLite or CPython.

    Browser execution is subject to the remote server's CORS policy.
    """
    headers = headers or {}
    if sys.platform == "emscripten":
        from pyodide.http import pyfetch  # type: ignore
        response = await pyfetch(url, method="GET", headers=headers)
        if response.status >= 400:
            body = await response.string()
            raise RuntimeError(f"HTTP {response.status} for {url}: {body[:300]}")
        return await response.json()

    # Keep this dependency-free in CPython.
    import urllib.request
    request = urllib.request.Request(url, headers=headers)

    def _load() -> Dict[str, Any]:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    return await asyncio.to_thread(_load)


def _openalex_url(query: str, start: date, config: Dict[str, Any]) -> str:
    params = {
        "search": query,
        "filter": f"from_publication_date:{start.isoformat()}",
        "sort": "-publication_date",
        "per_page": int(config.get("max_results_per_query", 12)),
    }
    key = (config.get("api_keys") or {}).get("openalex", "").strip()
    if key:
        params["api_key"] = key
    return "https://api.openalex.org/works?" + urlencode(params)


def _openalex_author_url(name: str, start: date, config: Dict[str, Any]) -> str:
    filters = f"raw_author_name.search:{name},from_publication_date:{start.isoformat()}"
    params = {
        "filter": filters,
        "sort": "-publication_date",
        "per_page": int(config.get("max_results_per_query", 12)),
    }
    key = (config.get("api_keys") or {}).get("openalex", "").strip()
    if key:
        params["api_key"] = key
    return "https://api.openalex.org/works?" + urlencode(params)


def parse_openalex_work(w: Dict[str, Any], matched_query: str = "") -> Dict[str, Any]:
    authorships = w.get("authorships") or []
    authors = []
    for a in authorships:
        author = (a or {}).get("author") or {}
        if author.get("display_name"):
            authors.append(author["display_name"])
    loc = w.get("primary_location") or {}
    source_obj = loc.get("source") or {}
    doi = w.get("doi") or ""
    link = doi or loc.get("landing_page_url") or w.get("id") or ""
    oa = w.get("open_access") or {}
    return {
        "id": w.get("id") or doi or normalize_text(w.get("title", "")),
        "doi": doi,
        "title": w.get("title") or w.get("display_name") or "Untitled",
        "authors": authors,
        "date": w.get("publication_date") or "",
        "year": w.get("publication_year"),
        "abstract": reconstruct_openalex_abstract(w.get("abstract_inverted_index")),
        "url": link,
        "pdf_url": loc.get("pdf_url") or "",
        "venue": source_obj.get("display_name") or "",
        "citation_count": int(w.get("cited_by_count") or 0),
        "open_access": bool(oa.get("is_oa")),
        "source": "OpenAlex",
        "matched_queries": [matched_query] if matched_query else [],
    }


async def collect_openalex(config: Dict[str, Any], start: date) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for query in config.get("query_families", []):
        try:
            data = await fetch_json(_openalex_url(query, start, config))
            rows.extend(parse_openalex_work(w, query) for w in data.get("results", []))
        except Exception as e:
            rows.append({"_error": f"OpenAlex query '{query}': {e}"})
        await asyncio.sleep(0.08)

    # Named-author watch. This catches papers from watched researchers even if the
    # paper title uses unexpected terminology.
    for person in config.get("watch_people", []):
        try:
            data = await fetch_json(_openalex_author_url(person, start, config))
            rows.extend(parse_openalex_work(w, f"author:{person}") for w in data.get("results", []))
        except Exception as e:
            rows.append({"_error": f"OpenAlex author '{person}': {e}"})
        await asyncio.sleep(0.08)
    return rows


def _s2_url(query: str, config: Dict[str, Any]) -> str:
    # Relevance search is intentionally bounded. The local date filter removes stale hits.
    fields = "title,abstract,url,authors,publicationDate,year,venue,citationCount,externalIds,openAccessPdf"
    params = {
        "query": query,
        "limit": min(100, int(config.get("max_results_per_query", 12))),
        "fields": fields,
        "year": f"{today_local().year - 1}-",
    }
    return "https://api.semanticscholar.org/graph/v1/paper/search?" + urlencode(params)


def parse_s2_paper(w: Dict[str, Any], matched_query: str = "") -> Dict[str, Any]:
    ext = w.get("externalIds") or {}
    doi = ext.get("DOI") or ""
    doi_url = f"https://doi.org/{doi}" if doi and not str(doi).startswith("http") else str(doi or "")
    oa = w.get("openAccessPdf") or {}
    return {
        "id": w.get("paperId") or doi_url or normalize_text(w.get("title", "")),
        "doi": doi_url,
        "title": w.get("title") or "Untitled",
        "authors": [a.get("name") for a in (w.get("authors") or []) if a.get("name")],
        "date": w.get("publicationDate") or (str(w.get("year")) if w.get("year") else ""),
        "year": w.get("year"),
        "abstract": w.get("abstract") or "",
        "url": doi_url or w.get("url") or "",
        "pdf_url": oa.get("url") or "",
        "venue": w.get("venue") or "",
        "citation_count": int(w.get("citationCount") or 0),
        "open_access": bool(oa.get("url")),
        "source": "Semantic Scholar",
        "matched_queries": [matched_query] if matched_query else [],
    }


async def collect_semantic_scholar(config: Dict[str, Any], start: date) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    headers: Dict[str, str] = {}
    key = (config.get("api_keys") or {}).get("semantic_scholar", "").strip()
    if key:
        headers["x-api-key"] = key
    for query in config.get("query_families", []):
        try:
            data = await fetch_json(_s2_url(query, config), headers=headers)
            for w in data.get("data", []):
                row = parse_s2_paper(w, query)
                d = parse_date(row.get("date"))
                if d is None or d >= start:
                    rows.append(row)
        except Exception as e:
            rows.append({"_error": f"Semantic Scholar query '{query}': {e}"})
        # Public S2 access is rate-limited; be conservative.
        await asyncio.sleep(0.16)
    return rows


def load_external_web_hits(path: str | Path, start: date) -> List[Dict[str, Any]]:
    """Load optional web/social hits produced by a compliant external search provider.

    Expected JSON: a list of dicts containing at least title and url. Optional fields:
    snippet, date, author, source.
    """
    p = Path(path)
    if not p.exists():
        return []
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return [{"_error": f"Could not read {p}: {e}"}]
    rows = []
    for i, hit in enumerate(raw if isinstance(raw, list) else []):
        d = parse_date(hit.get("date"))
        if d and d < start:
            continue
        rows.append({
            "id": hit.get("id") or hit.get("url") or f"external-{i}",
            "doi": hit.get("doi") or "",
            "title": hit.get("title") or "Untitled web result",
            "authors": [hit.get("author")] if hit.get("author") else [],
            "date": hit.get("date") or "",
            "year": d.year if d else None,
            "abstract": hit.get("snippet") or hit.get("abstract") or "",
            "url": hit.get("url") or "",
            "pdf_url": hit.get("pdf_url") or "",
            "venue": hit.get("site") or "",
            "citation_count": int(hit.get("citation_count") or 0),
            "open_access": bool(hit.get("open_access", False)),
            "source": hit.get("source") or "Web index",
            "matched_queries": hit.get("matched_queries") or [],
        })
    return rows


def deduplicate(rows: Sequence[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    errors = [r["_error"] for r in rows if r.get("_error")]
    clean = [r for r in rows if not r.get("_error") and r.get("title")]
    merged: List[Dict[str, Any]] = []
    by_doi: Dict[str, int] = {}
    by_title: Dict[str, int] = {}

    for r in clean:
        doi_key = normalize_text(r.get("doi", ""))
        title_key = normalize_text(r.get("title", ""))
        idx: Optional[int] = None
        if doi_key and doi_key in by_doi:
            idx = by_doi[doi_key]
        elif title_key and title_key in by_title:
            idx = by_title[title_key]
        else:
            # Small fuzzy safety net for punctuation/subtitle differences.
            for j, existing in enumerate(merged[-80:]):
                ex_key = normalize_text(existing.get("title", ""))
                if title_key and ex_key and difflib.SequenceMatcher(None, title_key, ex_key).ratio() >= 0.965:
                    idx = max(0, len(merged) - 80) + j
                    break

        if idx is None:
            idx = len(merged)
            merged.append(dict(r))
        else:
            e = merged[idx]
            srcs = set(str(e.get("source", "")).split(" + ")) | set(str(r.get("source", "")).split(" + "))
            e["source"] = " + ".join(sorted(s for s in srcs if s))
            e["matched_queries"] = sorted(set(e.get("matched_queries", [])) | set(r.get("matched_queries", [])))
            e["open_access"] = bool(e.get("open_access") or r.get("open_access"))
            e["citation_count"] = max(int(e.get("citation_count") or 0), int(r.get("citation_count") or 0))
            if len(r.get("abstract", "")) > len(e.get("abstract", "")):
                e["abstract"] = r.get("abstract", "")
            if not e.get("pdf_url") and r.get("pdf_url"):
                e["pdf_url"] = r["pdf_url"]
            if not e.get("url") and r.get("url"):
                e["url"] = r["url"]

        if doi_key:
            by_doi[doi_key] = idx
        if title_key:
            by_title[title_key] = idx
    return merged, errors


def _hits(text: str, terms: Sequence[str]) -> List[str]:
    t = normalize_text(text)
    out = []
    for term in terms:
        if normalize_text(term) in t:
            out.append(term)
    return sorted(set(out))


def _author_watch_hit(authors: Sequence[str], watch_people: Sequence[str]) -> Optional[str]:
    nauth = [normalize_text(a) for a in authors]
    for p in watch_people:
        np = normalize_text(p)
        if any(np == a or (np and np in a) or (a and a in np) for a in nauth):
            return p
    return None


def _recency_points(d: Optional[date], today: date) -> int:
    if d is None:
        return 0
    age = max(0, (today - d).days)
    if age <= 1:
        return 10
    if age <= 3:
        return 8
    if age <= 7:
        return 6
    if age <= 14:
        return 3
    return 1


def mvp_hint(text: str) -> str:
    t = normalize_text(text)
    rules = [
        (["geoprivacy", "differential privacy", "disclosure risk"],
         "Prototype on synthetic/public point data; compare privacy transforms against spatial utility metrics."),
        (["population mapping", "small area", "worldpop", "human settlement"],
         "Recreate a small-area estimator with WorldPop/GHSL/census-style open data for one county or district."),
        (["mobility", "travel time", "accessibility", "activity space"],
         "Build a small accessibility/mobility example with open points and a lightweight graph or travel-time matrix."),
        (["disease mapping", "spatial epidemiology", "outbreak", "hotspot", "cluster"],
         "Test the method on an open or synthetic disease-count grid; compare baseline and spatially aware results."),
        (["urban heat", "land surface temperature", "landsat", "sentinel", "earth observation", "remote sensing"],
         "Use a small open EO sample/derived table to reproduce the key feature-engineering or validation idea."),
        (["foundation model", "geoai", "transformer", "representation learning"],
         "Make a low-compute surrogate: reuse published embeddings/features or a tiny sample rather than training a large model."),
        (["graph neural", "network"],
         "Create a toy spatial graph from open points/polygons and test the message-passing or network statistic on a small sample."),
        (["bayesian", "uncertainty", "interpolation", "downscal"],
         "Prototype the estimator on a small synthetic surface and visualize uncertainty/calibration, keeping inference lightweight."),
        (["llm", "spatial reasoning", "agent"],
         "Prototype the workflow contract with small GeoJSON/metadata and deterministic checks before adding an optional model API."),
    ]
    for terms, hint in rules:
        if any(normalize_text(x) in t for x in terms):
            return hint
    return "Implement the paper's core transformation on a tiny open/synthetic dataset and compare it with a simple baseline."


def score_item(item: Dict[str, Any], config: Dict[str, Any], today: Optional[date] = None) -> Dict[str, Any]:
    today = today or today_local()
    text = " ".join([
        item.get("title", ""), item.get("abstract", ""), item.get("venue", ""),
        " ".join(item.get("matched_queries", [])),
    ])
    ignore_hits = _hits(text, config.get("ignore_terms", []))

    group_hits: Dict[str, List[str]] = {}
    groups_matched = 0
    total_interest_hits = 0
    for group, terms in (config.get("interest_groups") or {}).items():
        h = _hits(text, terms)
        group_hits[group] = h
        if h:
            groups_matched += 1
            total_interest_hits += min(4, len(h))

    watch = _author_watch_hit(item.get("authors", []), config.get("watch_people", []))
    d = parse_date(item.get("date"))

    # Interest score: multiple independent interest dimensions matter more than repeated keywords.
    interest = min(70, groups_matched * 12 + total_interest_hits * 3)
    interest += 15 if watch else 0
    interest += _recency_points(d, today)
    if item.get("open_access"):
        interest += 5
    if ignore_hits:
        interest -= 35
    interest = max(0, min(100, int(round(interest))))

    sig = config.get("prototype_signals") or {}
    open_hits = _hits(text, sig.get("open_data", []))
    impl_hits = _hits(text, sig.get("implementation", []))
    method_hits = _hits(text, sig.get("concrete_method", []))
    heavy_hits = _hits(text, sig.get("browser_heavy", []))

    proto = 20  # default: most methods can be tested on a tiny/synthetic dataset
    proto += min(20, len(open_hits) * 5)
    proto += 5 if item.get("open_access") else 0
    proto += min(30, len(impl_hits) * 6)
    proto += min(20, len(method_hits) * 4)
    proto += min(5, _recency_points(d, today) // 2)
    proto += 5 if item.get("pdf_url") else 0
    proto -= min(25, len(heavy_hits) * 7)
    # Concrete implementation artifacts make a method much easier to turn into an MVP.
    artifact_terms = {"package", "github", "repository", "notebook", "pypi", "software"}
    if artifact_terms.intersection(set(impl_hits)):
        proto += 12
    if len(impl_hits) >= 3:
        proto += 6
    if ignore_hits:
        proto -= 30
    proto = max(0, min(100, int(round(proto))))

    priority = int(round(0.58 * interest + 0.42 * proto))
    result = dict(item)
    result.update({
        "interest_score": interest,
        "prototype_score": proto,
        "priority_score": priority,
        "watch_person": watch or "",
        "interest_hits": group_hits,
        "open_data_hits": open_hits,
        "implementation_hits": impl_hits,
        "method_hits": method_hits,
        "heavy_compute_hits": heavy_hits,
        "ignore_hits": ignore_hits,
        "mvp_hint": mvp_hint(text),
    })
    return result


def item_key(item: Dict[str, Any]) -> str:
    doi = normalize_text(item.get("doi", ""))
    if doi:
        return "doi:" + doi
    title = normalize_text(item.get("title", ""))
    return "title:" + title[:220]


def filter_seen(items: Sequence[Dict[str, Any]], seen_path: str | Path = "seen_items.json") -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    seen = load_json(seen_path, default={}) or {}
    fresh = [x for x in items if item_key(x) not in seen]
    return fresh, seen


def update_seen(items: Sequence[Dict[str, Any]], seen: Dict[str, Any], seen_path: str | Path = "seen_items.json") -> None:
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    for x in items:
        seen[item_key(x)] = {"first_seen": seen.get(item_key(x), {}).get("first_seen", stamp), "title": x.get("title", "")}
    # Keep state bounded.
    if len(seen) > 8000:
        keys = list(seen.keys())[-8000:]
        seen = {k: seen[k] for k in keys}
    save_json(seen, seen_path)


async def run_scan(config: Dict[str, Any], include_seen: bool = False, seen_path: str | Path = "seen_items.json") -> Dict[str, Any]:
    today = today_local()
    start = today - timedelta(days=int(config.get("lookback_days", 4)))
    raw: List[Dict[str, Any]] = []
    if (config.get("sources") or {}).get("openalex", True):
        raw.extend(await collect_openalex(config, start))
    if (config.get("sources") or {}).get("semantic_scholar", True):
        raw.extend(await collect_semantic_scholar(config, start))
    external = (config.get("sources") or {}).get("external_web_hits_file")
    if external:
        raw.extend(load_external_web_hits(external, start))

    deduped, errors = deduplicate(raw)
    scored = [score_item(x, config, today=today) for x in deduped]
    scored.sort(key=lambda x: (x.get("priority_score", 0), x.get("prototype_score", 0), x.get("date", "")), reverse=True)
    scored = [x for x in scored if x.get("priority_score", 0) >= int(config.get("minimum_priority_score", 42))]

    seen = load_json(seen_path, default={}) or {}
    if include_seen:
        fresh = scored
    else:
        fresh = [x for x in scored if item_key(x) not in seen]

    return {
        "run_date": today.isoformat(),
        "window_start": start.isoformat(),
        "total_raw": len([r for r in raw if not r.get("_error")]),
        "total_deduped": len(deduped),
        "total_scored": len(scored),
        "items": fresh,
        "errors": errors,
        "seen_state": seen,
    }


def export_csv(items: Sequence[Dict[str, Any]], path: str | Path) -> None:
    fields = ["priority_score", "interest_score", "prototype_score", "date", "title", "authors", "venue", "source", "url", "pdf_url", "watch_person", "mvp_hint"]
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for x in items:
            row = {k: x.get(k, "") for k in fields}
            row["authors"] = "; ".join(x.get("authors", []))
            w.writerow(row)


def _safe_asciiish(s: str) -> str:
    # Core PDF Helvetica with WinAnsi supports most Western punctuation.
    return (s or "").encode("cp1252", errors="replace").decode("cp1252")


def _pdf_escape(s: str) -> str:
    s = _safe_asciiish(s)
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap(s: str, width: int) -> List[str]:
    s = re.sub(r"\s+", " ", (s or "").strip())
    return textwrap.wrap(s, width=width, break_long_words=False, break_on_hyphens=False) or [""]


def create_one_page_pdf(items: Sequence[Dict[str, Any]], path: str | Path, run_date: Optional[str] = None, max_items: int = 7) -> None:
    """Create a dependency-free, one-page Letter PDF with clickable article links."""
    run_date = run_date or today_local().isoformat()
    selected = list(items)[:max_items]
    page_w, page_h = 612, 792
    left, right = 42, 570
    y = 752.0
    content: List[str] = []
    annots: List[Tuple[float, float, float, float, str]] = []

    def text_line(text: str, x: float, y0: float, size: float, bold: bool = False) -> None:
        font = "/F2" if bold else "/F1"
        content.append(f"BT {font} {size:.1f} Tf 1 0 0 1 {x:.1f} {y0:.1f} Tm ({_pdf_escape(text)}) Tj ET")

    # Header
    text_line("GEOSPATIAL RESEARCH RADAR", left, y, 16, True)
    text_line(f"Morning brief | {run_date}", left, y - 20, 9, False)
    text_line("Priority = 58% interest fit + 42% MVP/Jupyter prototypeability", left, y - 34, 8, False)
    y -= 54
    content.append(f"0.6 w 0.75 G {left:.1f} {y:.1f} m {right:.1f} {y:.1f} l S")
    y -= 15

    if not selected:
        text_line("No new high-signal items met the threshold in this scan window.", left, y, 10, False)
    else:
        for rank, item in enumerate(selected, start=1):
            p = int(item.get("priority_score", 0))
            m = int(item.get("prototype_score", 0))
            date_s = str(item.get("date") or "")[:10]
            watch = item.get("watch_person") or ""
            meta = f"#{rank}  PRIORITY {p}  |  MVP {m}  |  {date_s or 'date n/a'}"
            if watch:
                meta += f"  |  WATCH: {watch}"
            text_line(meta, left, y, 7.6, True)
            y -= 11

            title_lines = _wrap(item.get("title", ""), 88)[:2]
            link_top = y + 3
            for line in title_lines:
                text_line(line, left, y, 9.2, True)
                y -= 11
            link_bottom = y + 1
            url = item.get("url") or item.get("pdf_url") or ""
            if url:
                annots.append((left, link_bottom, right, link_top + 9, url))

            auth = ", ".join(item.get("authors", [])[:4])
            if len(item.get("authors", [])) > 4:
                auth += " et al."
            source_line = " | ".join(x for x in [auth, item.get("venue", ""), item.get("source", "")] if x)
            for line in _wrap(source_line, 112)[:1]:
                text_line(line, left, y, 7.1, False)
                y -= 9

            hint = "MVP: " + (item.get("mvp_hint") or "")
            for line in _wrap(hint, 116)[:2]:
                text_line(line, left + 8, y, 7.5, False)
                y -= 9
            y -= 6
            if y < 70:
                break

    footer_y = 42
    content.append(f"0.4 w 0.82 G {left:.1f} {footer_y + 13:.1f} m {right:.1f} {footer_y + 13:.1f} l S")
    text_line("Sources: OpenAlex + Semantic Scholar + optional external web-index JSON. Titles are clickable.", left, footer_y, 6.8, False)
    text_line("LinkedIn/Google Scholar direct scraping is intentionally excluded; use sanctioned alerts/APIs or an external search index bridge.", left, footer_y - 9, 6.8, False)

    stream = "\n".join(content).encode("cp1252", errors="replace")

    objects: List[bytes] = []
    # 1 catalog, 2 pages, 3 page, 4 Helvetica, 5 Helvetica-Bold, 6 contents, annotations follow.
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    annot_refs = " ".join(f"{7+i} 0 R" for i in range(len(annots)))
    annots_clause = f" /Annots [{annot_refs}]" if annots else ""
    page_obj = f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_w} {page_h}] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R{annots_clause} >>"
    objects.append(page_obj.encode("latin1"))
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    objects.append(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream")
    for x1, y1, x2, y2, url in annots:
        uri = quote(str(url), safe=":/?#[]@!$&'()*+,;=%")
        obj = f"<< /Type /Annot /Subtype /Link /Rect [{x1:.1f} {y1:.1f} {x2:.1f} {y2:.1f}] /Border [0 0 0] /A << /S /URI /URI ({_pdf_escape(uri)}) >> >>"
        objects.append(obj.encode("cp1252", errors="replace"))

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{i} 0 obj\n".encode("ascii"))
        out.extend(obj)
        out.extend(b"\nendobj\n")
    xref = len(out)
    out.extend(f"xref\n0 {len(objects)+1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    out.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii"))
    Path(path).write_bytes(bytes(out))


def create_one_page_html(items: Sequence[Dict[str, Any]], path: str | Path, run_date: Optional[str] = None, max_items: int = 7) -> None:
    run_date = run_date or today_local().isoformat()
    cards = []
    for rank, x in enumerate(list(items)[:max_items], start=1):
        authors = ", ".join(x.get("authors", [])[:4]) + (" et al." if len(x.get("authors", [])) > 4 else "")
        url = html.escape(x.get("url") or x.get("pdf_url") or "#", quote=True)
        title = html.escape(x.get("title", ""))
        hint = html.escape(x.get("mvp_hint", ""))
        meta = html.escape(" | ".join(v for v in [str(x.get("date", ""))[:10], authors, x.get("venue", ""), x.get("source", "")] if v))
        watch = f"<span class='watch'>WATCH: {html.escape(x.get('watch_person',''))}</span>" if x.get("watch_person") else ""
        cards.append(f"""
        <article>
          <div class='score'>#{rank} PRIORITY {x.get('priority_score',0)} &nbsp; MVP {x.get('prototype_score',0)} {watch}</div>
          <a class='title' href='{url}' target='_blank'>{title}</a>
          <div class='meta'>{meta}</div>
          <div class='mvp'><b>MVP:</b> {hint}</div>
        </article>""")
    if not cards:
        cards = ["<p>No new high-signal items met the threshold in this scan window.</p>"]
    doc = f"""<!doctype html>
<html><head><meta charset='utf-8'><title>Geospatial Research Radar {run_date}</title>
<style>
@page {{ size: Letter; margin: 0.5in; }}
body {{ font-family: Arial, Helvetica, sans-serif; margin: 0.5in; color: #111; max-width: 8in; }}
h1 {{ font-size: 20px; margin: 0; }}
.sub {{ font-size: 10px; margin: 3px 0 12px; color: #444; border-bottom: 1px solid #bbb; padding-bottom: 8px; }}
article {{ margin: 0 0 10px; break-inside: avoid; }}
.score {{ font-size: 9px; font-weight: 700; letter-spacing: .25px; }}
.title {{ display: block; font-size: 11px; font-weight: 700; color: #111; text-decoration: none; margin: 2px 0; }}
.meta {{ font-size: 8px; color: #555; }}
.mvp {{ font-size: 9px; margin: 2px 0 0 8px; }}
.watch {{ margin-left: 8px; }}
footer {{ border-top: 1px solid #ccc; margin-top: 8px; padding-top: 5px; font-size: 7.5px; color: #555; }}
</style></head><body>
<h1>GEOSPATIAL RESEARCH RADAR</h1>
<div class='sub'>Morning brief | {html.escape(run_date)} | Priority = 58% interest fit + 42% MVP/Jupyter prototypeability</div>
{''.join(cards)}
<footer>Sources: OpenAlex + Semantic Scholar + optional external web-index JSON. Direct LinkedIn/Google Scholar scraping is intentionally excluded.</footer>
</body></html>"""
    Path(path).write_text(doc, encoding="utf-8")


def top_summary(items: Sequence[Dict[str, Any]], n: int = 10) -> str:
    lines = []
    for i, x in enumerate(list(items)[:n], start=1):
        lines.append(f"{i:>2}. P{x.get('priority_score',0):02d} MVP{x.get('prototype_score',0):02d} | {x.get('title','')} | {x.get('url','')}")
    return "\n".join(lines)


def make_external_search_queries(config: Dict[str, Any]) -> List[Dict[str, str]]:
    """Queries suitable for a sanctioned/commercial search API outside JupyterLite.

    These do not fetch LinkedIn directly; they are intended for a web search index that
    is authorized to return indexed public pages.
    """
    rows = []
    for person in config.get("watch_people", []):
        rows.append({"kind": "linkedin_index", "query": f'site:linkedin.com/posts "{person}" geospatial OR GIS OR GeoAI'})
        rows.append({"kind": "scholar_web", "query": f'"{person}" geospatial spatial GIS 2026'})
    for q in config.get("query_families", [])[:6]:
        rows.append({"kind": "researchgate_index", "query": f'site:researchgate.net/publication {q}'})
    return rows
