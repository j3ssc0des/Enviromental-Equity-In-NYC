# NYC Environmental Atlas

[View the deployed site](https://j3ssc0des.github.io/Enviromental-Equity-In-NYC)

An expanding, source-transparent atlas of New York City environmental conditions. The first module compares the 2005 and 2015 NYC Street Tree Censuses with 2020–2024 ACS five-year income context at 2010 Neighborhood Tabulation Area geography. Source years are displayed separately and the ACS release is refreshed by the build pipeline.

## Current module

- Street-tree counts and density
- Historical tree-count change
- ACS household-income context with coverage metadata
- A clearly labeled project screening score
- A clearly labeled tree-and-income heat proxy
- A compact map-first interface with expandable neighborhood details
- A persistent interpretation sidebar with source-bound neighborhood narratives
- An optional server-side, source-grounded AI interpretation with a calculation-based fallback
- A validated GeoJSON snapshot used by the map, rankings, findings, and localhost preview

Street trees are not total canopy. The proxy is not measured temperature or NYC's official Heat Vulnerability Index. Read [methodology](docs/methodology.md) before interpreting results.

Airports, parks, cemeteries, islands, correctional facilities, and other areas with fewer than 100 ACS households remain visible for geographic context but are excluded from residential investment rankings, priority markers, and heat-proxy comparisons.

## Roadmap

The [data catalog](docs/data-catalog.md) tracks official heat, flooding, canopy, air, pollution, water, health, and community-vulnerability sources. A dataset is promoted only after its native geography, uncertainty, transformation, missingness behavior, and update cadence are documented and tested.

The interpretation sidebar supports a server-side AI explanation layer. The browser sends only an NTA code and metric; the server reloads validated atlas records, supplies source metadata, and returns qualitative prose beside deterministic values and citations. If the endpoint is missing, slow, invalid, or unavailable, the current calculation-backed narrative remains visible. API keys never enter the GitHub Pages client. See [AI analysis architecture and deployment](docs/ai-analysis.md).

## Reliability

- `data/sources.json` is the source registry.
- The project data-audit skill checks availability and schema drift.
- Pull requests build from official sources and validate output without deploying.
- `main` deploys to GitHub Pages only after rebuilding and validating.
- A weekly scheduled build detects upstream changes.
- Demo fallback is forbidden in CI and deployment.

## Local build

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python .skillshare/skills/audit-nyc-environment-data/scripts/audit_sources.py
python nyc_trees_analysis.py
python scripts/validate_build.py
npm test
python3 -m http.server 8000
```

Then open `http://127.0.0.1:8000/`. Rankings read the validated GeoJSON directly and fail closed if it is unavailable, so the UI cannot silently fall back to old embedded defaults.

## Primary sources

- [NYC Street Tree Census 2015](https://data.cityofnewyork.us/d/uvpi-gqnh)
- [NYC Street Tree Census 2005](https://data.cityofnewyork.us/d/29bw-z7pj)
- [2010 tract-to-NTA crosswalk](https://data.cityofnewyork.us/d/8ius-dhrr)
- [2020–2024 ACS five-year API](https://api.census.gov/data/2024/acs/acs5.html)
