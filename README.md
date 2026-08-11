# NYC Environmental Atlas

[View the deployed site](https://j3ssc0des.github.io/Enviromental-Equity-In-NYC)

An expanding, source-transparent atlas of New York City environmental conditions. It currently presents the 2005–06 and 2015–16 NYC Street Tree Censuses on 2010 Neighborhood Tabulation Areas and NYC DOHMH's official 2023 Heat Vulnerability Index on its native 2020 NTA geography.

## Current module

- Street-tree counts and density
- Historical tree-count change
- Official 2023 Heat Vulnerability Index scores and published component values
- Separate, explicitly labeled 2010 and 2020 NTA geographies
- A compact map-first interface with expandable neighborhood details
- A persistent interpretation sidebar with source-bound neighborhood narratives
- A predictive, keyboard-accessible neighborhood search that preserves location across metrics
- Combined location reports with separate 2010 tree and 2020 heat records
- A deterministic explanation engine that runs entirely in the browser with no API key or usage fees
- Validated GeoJSON products used by the map, findings, downloads, and localhost preview

Street trees are not total canopy, and an HVI score of 1 does not mean no heat risk. Read [methodology](docs/methodology.md) before interpreting results.

## Roadmap

The [data catalog](docs/data-catalog.md) tracks official heat, flooding, canopy, air, pollution, water, health, and community-vulnerability sources. A dataset is promoted only after its native geography, uncertainty, transformation, missingness behavior, and update cadence are documented and tested.

The optional interpretation disclosure uses transparent rules, links directly to public sources, and states each metric's limitations. It runs locally in the visitor's browser, so the deployed site needs no API key, serverless function, paid AI service, or credit card.

## Reliability

- `data/sources.json` is the source registry.
- The project data-audit skill checks availability and schema drift.
- Pull requests build from official sources and validate output without deploying.
- `main` deploys to GitHub Pages only after rebuilding and validating.
- A weekly scheduled build detects upstream changes.
- Builds fail closed when an official source is unavailable; there is no demo fallback.
- Playwright exercises metric switching, legends, map clicks, search replacement, report downloads, and mobile layout in Chromium.

## Local build

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python .skillshare/skills/audit-nyc-environment-data/scripts/audit_sources.py
python nyc_trees_analysis.py
python scripts/validate_build.py
npm test
npm run test:e2e
python3 -m http.server 8000
```

Then open `http://127.0.0.1:8000/`. The interface reads validated GeoJSON directly and fails closed if it is unavailable, so it cannot silently fall back to old embedded defaults.

## Primary sources

- [NYC Street Tree Census 2015](https://data.cityofnewyork.us/d/uvpi-gqnh)
- [NYC Street Tree Census 2005](https://data.cityofnewyork.us/d/29bw-z7pj)
- [2010 tract-to-NTA crosswalk](https://data.cityofnewyork.us/d/8ius-dhrr)
- [NYC DOHMH Heat Vulnerability Index 2023](https://a816-dohbesp.nyc.gov/IndicatorPublic/data-features/hvi/)
- [NYC Planning 2020 Neighborhood Tabulation Areas](https://data.cityofnewyork.us/d/9nt8-h7nd)
