# NYC environmental data catalog

Last reviewed: 2026-08-11. “Available” means the dataset is integrated, validated, and visible. “Catalogued” means it is documented but intentionally absent from neighborhood metrics until it can be shown on its native geography.

| Domain | Dataset | Publisher | Native geography | Role |
|---|---|---|---|---|
| Green space | 2005 and 2015 Street Tree Census | NYC Parks | Tree point / 2010 NTA fields | Available |
| Canopy | Previous 2010–2017 candidate (`by9k-vhck`) | NYC Parks | Published product | Retired; source ID unavailable, replacement research required |
| Heat | 2023 Heat Vulnerability Index | NYC DOHMH | 2020 NTA | Available; direct code join to official 2020 NTA polygons |
| Flooding | NYC Flood Vulnerability Index (`mrjc-v9pm`) | NYC MOCEJ | Census tract | Published on native tracts; present storm-surge map plus official scenario fields |
| Air | Environment & Health Data Portal (`c3uy-2p5r`) | NYC DOHMH | UHF42 and other areas | Catalogued; not shown at NTA level |
| Income | ACS five-year B19013 | US Census Bureau | Census tract | Catalogued; not displayed because the previous 2010-NTA conversion was project-created |
| Demographics | ACS poverty, age, race/ethnicity, disability, housing burden | US Census Bureau | Census tract | Planned |
| Climate resources | Cooling centers, fountains, spray showers | NYC | Point | Planned |
| Pollution | State cleanup sites, brownfields, waste transfer facilities | NYS/NYC | Point/polygon | Planned |
| Water | CSO outfalls, harbor sampling, beach advisories | NYC DEP/DOHMH | Point/site | Planned |

Each integrated dataset needs a source URL, dataset identifier, reference period, retrieval timestamp, unit, native geography, transformation method, missingness rate, and update cadence.

The deployed products contain no project-created crosswalk estimate or combined screening score. Tree density and change are exact arithmetic from published census counts and official land area; HVI values are published directly by NYC DOHMH; FVI values are published directly by NYC MOCEJ on census tracts. A missing flood-scenario score is displayed as unavailable, never as zero risk.

## Future income and multi-factor screening module

Income context remains planned, but it will be published only after the project documents an official source, reference period, native geography, uncertainty, missingness, and any required geographic transformation. A tract-derived value must never be labeled as an official NTA median.

A future multi-factor screening view must keep every official input visible and independently selectable. Any normalization, direction, weight, aggregation, missing-data rule, and sensitivity test must be documented and reproducible. Its result must be labeled as a project-created screening method—not an official NYC score, risk assessment, eligibility decision, or causal finding.
