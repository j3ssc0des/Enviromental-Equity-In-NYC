# Methodology and limitations

This site is an environmental-data exploration tool. It is not a risk assessment, regulatory designation, or causal analysis.

## Core geography

Tree mode uses 2010 Neighborhood Tabulation Areas (NTAs), matching the codes carried by the 2005–06 and 2015–16 Street Tree Census products. Heat mode uses 2020 NTAs, matching the official 2023 HVI file. The two boundary systems are switched as separate layers and are never treated as interchangeable.

When a visitor switches between tree and heat modes, the interface preserves the selected map location and opens the polygon from the other dataset that contains that point. This is a navigation aid, not a data crosswalk: the panel and report continue to identify each record by its own NTA name, code, vintage, and source year.

The downloadable combined location report applies the same point-in-polygon navigation rule. It presents the resulting 2010 tree NTA and 2020 heat NTA as separate records with separate analyses and source notes; it does not merge, average, or transfer values between the boundary systems.

## Street trees

Tree counts come from the NYC Parks 2005–06 and 2015–16 Street Tree Censuses. The interface lets you switch the active census wave while retaining the same NTA geography. Density is count divided by land area, not total polygon area. Street-tree counts do not represent park trees, private trees, forest, wetlands, or total canopy.

The official 2005 file contains 592,372 records with a non-null NTA field, but 24,027 of those records contain only a blank code. The project maps 568,345 records to valid NTAs, or 95.9% coverage. Blank-code records are excluded from neighborhood change rather than guessed into a geography. The generated snapshot publishes both the unassigned count and mapping coverage.

All official NTA records remain available on the map. Comparisons described as neighborhood rankings, citywide neighborhood benchmarks, or borough-average neighborhood density exclude 2010 NTA special-purpose codes ending in `98` or `99`, which represent areas such as airports, Rikers Island, parks, and cemeteries. Their Street Tree Census count is not a measure of all trees or shade within those areas.

## Air quality

NYC DOHMH annual PM2.5 estimates are published for health geographies such as UHF42 areas. They are modeled area estimates, not neighborhood monitors. Values must never be assigned by fuzzy name matching. A future NTA conversion must use a documented spatial or population-weighted crosswalk and report coverage.

## Heat

The atlas displays NYC DOHMH's official 2023 Heat Vulnerability Index directly. The source file's 2020 NTA codes are joined directly to NYC Planning's 2020 NTA polygons. No crosswalk, interpolation, or project-created neighborhood heat score is used. HVI ranges from 1 (lowest relative vulnerability) to 5 (highest); a lower score does not mean no heat risk. Surface temperature, green space, and household air-conditioning values shown in the panel are the values published in the same official HVI file.

## Interpretation

Mapped associations do not prove that trees caused heat outcomes or that observed differences reflect a specific investment history.

The optional neighborhood interpretation is generated locally from explicit rules in `assets/interpretation.mjs`; it does not call an AI model or remote interpretation service. Tree analysis reports a percentile among standard neighborhood NTAs, an area-weighted borough comparison, and exact recorded change. Heat analysis reports the official score distribution and compares the source file’s published temperature, green-space, and air-conditioning values with medians calculated across the same 197 HVI-covered 2020 NTAs. These comparisons are descriptive arithmetic, not new environmental measurements or causal findings. Automated tests run every published neighborhood through the relevant rules and reject causal or hazardous language.

## Flood vulnerability

Flood mode uses New York City's official Flood Vulnerability Index (`mrjc-v9pm`) directly on the dataset's census-tract polygons. The default flood layer is the published present storm-surge FVI (`ss_cur`), scored from 1 to 5. The inspector also reports the Flood Susceptibility to Harm and Recovery Index and the published 2050s and 2080s storm-surge scenarios. No tract-to-NTA conversion is performed.

Most tracts do not have a score for every hazard scenario. Missing means that the official dataset does not publish a score for that tract and scenario; it is not converted to zero, “low risk,” or “safe.” The FVI is an area-level relative index, not a parcel flood map, insurance determination, or prediction of a specific event.

## Planned income and screening analysis

Income context and multi-factor screening are planned, but are not part of the current published metrics. Income will retain its official source geography and reference period unless a documented, tested conversion is necessary; a converted value will be clearly identified as an estimate rather than an official neighborhood statistic.

If a combined screening method is introduced, the interface will expose its component indicators and calculation choices. The documentation will state normalization, direction, weights, missing-data handling, geographic compatibility, year alignment, and sensitivity to alternate weights. The result will be described as a project-created exploratory method and will not be presented as an official score or funding recommendation.
