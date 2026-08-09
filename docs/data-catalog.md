# NYC environmental data catalog

Last reviewed: 2026-08-09. “Available” means the dataset is integrated, validated, and visible. “Catalogued” means it is documented but intentionally absent from neighborhood metrics until its geography is handled correctly.

| Domain | Dataset | Publisher | Native geography | Role |
|---|---|---|---|---|
| Green space | 2005 and 2015 Street Tree Census | NYC Parks | Tree point / 2010 NTA fields | Available |
| Canopy | Previous 2010–2017 candidate (`by9k-vhck`) | NYC Parks | Published product | Retired; source ID unavailable, replacement research required |
| Heat | Heat Vulnerability Index Rankings (`4mhf-duep`) | NYC DOHMH | ZIP/ZCTA | Next; no NTA conversion yet |
| Flooding | NYC Flood Vulnerability Index (`mrjc-v9pm`) | NYC | Census tract | Next; crosswalk required |
| Air | Environment & Health Data Portal (`c3uy-2p5r`) | NYC DOHMH | UHF42 and other areas | Catalogued; not shown at NTA level |
| Income | ACS 2020–2024 B19013 and B11001 | US Census Bureau via Census Reporter | Census tract | Available; household-weighted NTA approximation |
| Demographics | ACS poverty, age, race/ethnicity, disability, housing burden | US Census Bureau | Census tract | Planned |
| Climate resources | Cooling centers, fountains, spray showers | NYC | Point | Planned |
| Pollution | State cleanup sites, brownfields, waste transfer facilities | NYS/NYC | Point/polygon | Planned |
| Water | CSO outfalls, harbor sampling, beach advisories | NYC DEP/DOHMH | Point/site | Planned |

Each integrated dataset needs a source URL, dataset identifier, reference period, retrieval timestamp, unit, native geography, transformation method, missingness rate, and update cadence.

The current deployed income release is the 2020–2024 ACS five-year estimate, released by the Census Bureau on January 29, 2026. The source audit reads the latest available release and records its end year in every generated neighborhood row.
