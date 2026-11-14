# EE467 Group Project 3, Team 3, Project 1
Is India's electricity transition changing the shape of demand and supply?

Subham Agrawal (23B3919), Manya Unnat Shah (23B3969), Divyanshu Gupta (23B0306)

## How to run
Python 3 with the packages in `requirements.txt`. From this folder run `./run_all.sh`.
It rebuilds `data/processed`, `output/tables` and `output/figures` from `data/raw` and `data/external`, writes the appendix table for the report, and checks the headline numbers quoted in the report against the outputs. It takes under a minute. Random seeds are fixed.
The report is in `report/report.tex` (compile with pdflatex twice).

## Raw files (`data/raw`, checksums in `SHA256SUMS.txt`)
- `ember_india_monthly.csv`: Ember, India Electricity Data, monthly state file, official download from https://files.ember-energy.org/public-downloads/india_monthly_full_release_long_format.csv (14 Nov 2026). Jan 2019 to Nov 2025, 238,200 rows. CC BY 4.0.
- `gridindia_daily_psp.csv` and `gridindia_daily_psp_metadata.json`: Grid-India daily power supply position reports, Apr 2019 to Oct 2026, as compiled by R. Andrew (https://robbieandrew.github.io/india/), downloaded 5 Nov 2026. Grid-India publishes one report per day, so the compilation was used for access.
- `mnre_re_statistics_2024_25.pdf`: MNRE, Renewable Energy Statistics 2024-25 (Nov 2025), downloaded 14 Nov 2026.

## Typed tables (`data/external`)
- `cea_annual_state.csv`: state energy requirement and peak demand. FY2024-25 and FY2025-26 from CEA LGBR 2026-27 Annex II and III; FY2019-20 and FY2020-21 from LGBR and the Lok Sabha unstarred question 2608 annexure. Blank peak cells are north-eastern FY2024-25 values that are not used.
- `cea_national_annual.csv`: All-India energy requirement and peak demand, CEA LGBR 2026-27.
- `mnre_state_capacity_31mar2025.csv`: MNRE Tables 8.2 (wind) and 8.3 (solar split), as on 31.03.2025, typed from the PDF above. Column totals match the published totals.
- `state_context.csv`: Census 2011 population, 2026 projection (Technical Group on Population Projections), and per capita GSDP at constant prices FY2024-25 (MoSPI, via StatisticsTimes).

## Code (`code`)
- `common.py`: shared loading, windows and definitions.
- `01_prepare.py`: cleaning, merges, outlier screen and cross-checks between sources.
- `02_sq1_demand.py`: SQ1, demand level and shape.
- `03_sq2_supply.py`: SQ2, capacity against output, seasonal match, net position and the what-if scenarios.
- `04_sq3_typology.py`: SQ3, PCA, k-means, stability and sensitivity checks (argument: number of groups, default 6).
- `05_figures.py`: all report figures.
- `06_report_tables.py`: appendix state table for the report.
- `07_verify_numbers.py`: checks headline numbers in the report against the output tables.
- `group_names.csv`: names given to the six groups.
