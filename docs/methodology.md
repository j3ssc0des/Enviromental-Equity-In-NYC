# Methodology and limitations

This site is an environmental-data exploration tool. It is not a risk assessment, regulatory designation, or causal analysis.

## Core geography

Tree mode uses 2010 Neighborhood Tabulation Areas (NTAs), matching the codes carried by the 2005–06 and 2015–16 Street Tree Census products. Heat mode uses 2020 NTAs, matching the official 2023 HVI file. The two boundary systems are switched as separate layers and are never treated as interchangeable.

## Street trees

Tree counts come from the NYC Parks 2005–06 and 2015–16 Street Tree Censuses. The interface lets you switch the active census wave while retaining the same NTA geography. Density is count divided by land area, not total polygon area. Street-tree counts do not represent park trees, private trees, forest, wetlands, or total canopy.

The official 2005 file contains 592,372 records with a non-null NTA field, but 24,027 of those records contain only a blank code. The project maps 568,345 records to valid NTAs, or 95.9% coverage. Blank-code records are excluded from neighborhood change rather than guessed into a geography. The generated snapshot publishes both the unassigned count and mapping coverage.

## Air quality

NYC DOHMH annual PM2.5 estimates are published for health geographies such as UHF42 areas. They are modeled area estimates, not neighborhood monitors. Values must never be assigned by fuzzy name matching. A future NTA conversion must use a documented spatial or population-weighted crosswalk and report coverage.

## Heat

The atlas displays NYC DOHMH's official 2023 Heat Vulnerability Index directly. The source file's 2020 NTA codes are joined directly to NYC Planning's 2020 NTA polygons. No crosswalk, interpolation, or project-created neighborhood heat score is used. HVI ranges from 1 (lowest relative vulnerability) to 5 (highest); a lower score does not mean no heat risk. Surface temperature, green space, and household air-conditioning values shown in the panel are the values published in the same official HVI file.

## Interpretation

Mapped associations do not prove that trees caused heat outcomes or that observed differences reflect a specific investment history.

The optional neighborhood interpretation is generated locally from explicit rules in `assets/interpretation.mjs`; it does not call an AI model or remote interpretation service. It compares tree density with the exact citywide density derived from the published tree counts and official land areas, describes historical tree-count direction, and explains the official HVI scale. Automated tests run every published neighborhood through the relevant rules and reject causal or hazardous language.
