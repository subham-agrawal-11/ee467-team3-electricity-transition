#!/bin/bash
# Rebuilds every processed file, table and figure from data/raw and data/external.
set -e
cd "$(dirname "$0")"
mkdir -p data/processed output/tables output/figures
python3 code/01_prepare.py
python3 code/02_sq1_demand.py
python3 code/03_sq2_supply.py
python3 code/04_sq3_typology.py 6
python3 code/05_figures.py
python3 code/06_report_tables.py
python3 code/07_verify_numbers.py
