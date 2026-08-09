# Methodology and limitations

This site is an environmental screening and exploration tool. It is not a risk assessment, regulatory designation, or causal analysis.

## Core geography

The current map uses 2010 Neighborhood Tabulation Areas (NTAs) because the 2005 and 2015 Street Tree Census products align most closely with that geography. Every metric must retain its native geography and reference year. Data converted to an NTA is marked as estimated and documents the conversion method.

## Street trees

Tree counts come from the NYC Parks 2005 and 2015 Street Tree Censuses. Density is count divided by land area, not total polygon area. Street-tree counts do not represent park trees, private trees, forest, wetlands, or total canopy.

The official 2005 file contains 592,372 records with a non-null NTA field, but 24,027 of those records contain only a blank code. The project maps 568,345 records to valid NTAs, or 95.9% coverage. Blank-code records are excluded from neighborhood change rather than guessed into a geography. The generated snapshot publishes both the unassigned count and mapping coverage.

## Income

Income comes from the latest American Community Survey five-year estimate (tables B19013 and B11001), accessed through Census Reporter. The deployed release is 2020–2024. Current census tracts are assigned to 2010 NTAs by representative-point spatial crosswalk, then tract medians are household-weighted. The interface keeps the ACS vintage separate from the 2015 tree year. Median values are not additive, so the result is an approximation rather than an official NTA median.

## Air quality

NYC DOHMH annual PM2.5 estimates are published for health geographies such as UHF42 areas. They are modeled area estimates, not neighborhood monitors. Values must never be assigned by fuzzy name matching. A future NTA conversion must use a documented spatial or population-weighted crosswalk and report coverage.

## Heat

The project's original “heat vulnerability” value was a tree-and-income proxy, not measured heat. The interface must label it as a proxy until it is replaced by the official NYC Heat Vulnerability Index. Official HVI values should remain in their published geography or use an explicit spatial crosswalk.

## Screening score

Any combined score is project-defined. It must expose its component values and weights, avoid authoritative labels such as “safe,” “healthy,” or “hazardous,” and be tested for sensitivity to alternative weights. Missing or estimated inputs must not be silently replaced with citywide defaults.

## Interpretation

Mapped associations do not prove that income caused tree coverage, that trees caused local air quality, or that observed differences reflect a specific investment history. Narrative text uses “associated with” language unless a cited study supports a causal statement.

When the optional AI endpoint is configured, the browser sends only the selected NTA code and metric. The server independently reloads the validated snapshot and computes all evidence and source links. The model writes only a short qualitative interpretation and is prohibited from emitting figures, URLs, causal claims, or funding recommendations. Exact values and source years remain deterministic interface elements. Invalid model output, timeout, missing configuration, or any endpoint error restores the calculation-based narrative without hiding the neighborhood data. See [AI analysis architecture](ai-analysis.md).

## Community investment eligibility

Airports, parks, cemeteries, islands, correctional facilities, and other planning areas with fewer than 100 ACS households remain visible as geographic context. They are labeled non-residential and excluded from community screening scores, heat-proxy rankings, priority markers, and borough investment comparisons. This prevents land-intensive infrastructure areas from displacing residential communities in rankings.
