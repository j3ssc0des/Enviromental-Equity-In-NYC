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

The atlas does not currently calculate heat vulnerability or present its tree-and-income screening score as a heat measure. A future heat module should use NYC's official Heat Vulnerability Index in its published geography or an explicit spatial crosswalk.

## Screening score

Any combined score is project-defined. It must expose its component values and weights, avoid authoritative labels such as “safe,” “healthy,” or “hazardous,” and be tested for sensitivity to alternative weights. Missing or estimated inputs must not be silently replaced with citywide defaults.

## Interpretation

Mapped associations do not prove that income caused tree coverage, that trees caused local air quality, or that observed differences reflect a specific investment history. Narrative text uses “associated with” language unless a cited study supports a causal statement.

The neighborhood interpretation is generated locally from explicit rules in `assets/interpretation.mjs`; it does not call an AI model or remote interpretation service. The rules compare tree density with the area-weighted eligible-area average, income with the eligible-area median, historical tree-count direction, and the published project scores. Each metric receives a fixed limitation statement and links to its public source. Automated tests run every neighborhood through every metric and reject causal, hazardous, or prescriptive funding language.

## Community investment eligibility

Airports, parks, cemeteries, islands, correctional facilities, and other planning areas with fewer than 100 ACS households remain visible as geographic context. They are labeled non-residential and excluded from community screening scores, priority markers, and borough investment comparisons. This prevents land-intensive infrastructure areas from displacing residential communities in rankings.
