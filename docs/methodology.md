# Methodology and limitations

This site is an environmental screening and exploration tool. It is not a risk assessment, regulatory designation, or causal analysis.

## Core geography

The current map uses 2010 Neighborhood Tabulation Areas (NTAs) because the 2005 and 2015 Street Tree Census products align most closely with that geography. Every metric must retain its native geography and reference year. Data converted to an NTA is marked as estimated and documents the conversion method.

## Street trees

Tree counts come from the NYC Parks 2005 and 2015 Street Tree Censuses. Density is count divided by land area, not total polygon area. Street-tree counts do not represent park trees, private trees, forest, wetlands, or total canopy.

## Income

Income should come from the 2011–2015 American Community Survey five-year estimate (table B19013) to match the 2015 tree snapshot. Census-tract estimates are converted to 2010 NTAs and must include the ACS vintage, aggregation method, coverage, and margin-of-error limitation. Median values are not additive; an NTA estimate derived from tract medians is an approximation.

## Air quality

NYC DOHMH annual PM2.5 estimates are published for health geographies such as UHF42 areas. They are modeled area estimates, not neighborhood monitors. Values must never be assigned by fuzzy name matching. A future NTA conversion must use a documented spatial or population-weighted crosswalk and report coverage.

## Heat

The project's original “heat vulnerability” value was a tree-and-income proxy, not measured heat. The interface must label it as a proxy until it is replaced by the official NYC Heat Vulnerability Index. Official HVI values should remain in their published geography or use an explicit spatial crosswalk.

## Screening score

Any combined score is project-defined. It must expose its component values and weights, avoid authoritative labels such as “safe,” “healthy,” or “hazardous,” and be tested for sensitivity to alternative weights. Missing or estimated inputs must not be silently replaced with citywide defaults.

## Interpretation

Mapped associations do not prove that income caused tree coverage, that trees caused local air quality, or that observed differences reflect a specific investment history. Narrative text uses “associated with” language unless a cited study supports a causal statement.

## Community investment eligibility

Airports, parks, cemeteries, islands, correctional facilities, and other planning areas with fewer than 100 ACS households remain visible as geographic context. They are labeled non-residential and excluded from community screening scores, heat-proxy rankings, priority markers, and borough investment comparisons. This prevents land-intensive infrastructure areas from displacing residential communities in rankings.
