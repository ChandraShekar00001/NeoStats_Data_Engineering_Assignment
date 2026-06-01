# NeoStats Data Engineering Assignment

## Project Overview

This repository contains the NeoStats Data Engineering Assignment: an end-to-end data engineering solution built to ingest, clean, transform, validate, and analyze retail transaction datasets. The pipeline produces cleaned datasets, KPI summaries, duplicate transaction analysis, and Power BI-ready outputs.

## Business Problem

Retail stakeholders require accurate transaction-level reporting to measure product and regional performance. The raw data contained inconsistencies, duplicates, and PII that threatened reporting accuracy and compliance. This project resolves data quality issues, quantifies financial impact from duplicates, and delivers reliable KPIs and dashboard-ready outputs.

## Dataset Description

The project uses an Excel workbook with the following sheets:

- `product_details`
- `retail_data1`
- `retail_data2`

Fields include product identifiers, product names, category, city, transaction ID, revenue, transaction date, and customer contact fields (email, phone).

## Data Quality Issues

Key issues found during profiling:

- Missing price values
- Inconsistent product naming conventions
- Inconsistent category values
- Mixed date formats
- Duplicate transaction IDs
- Presence of PII fields (email and phone)

## Pipeline Architecture

High-level flow:

- Ingest: Read Excel sheets using Pandas/OpenPyXL
- Validate: Basic schema and type checks
- Clean: Standardize names, normalize dates, handle missing values
- Deduplicate: Detect and resolve duplicate transaction IDs
- Mask PII: Anonymize email and phone fields
- Transform: Calculate revenue and KPIs
- Export: Write cleaned CSVs and KPI summaries for Power BI

Simple diagram:

```
Excel -> Ingestion -> Validation -> Cleaning -> Deduplication -> PII Masking -> KPI Calc -> Output (CSV, KPI)
```

## Data Cleaning & Transformation Steps

1. Standardize column names and types.
2. Normalize date columns to ISO format (YYYY-MM-DD).
3. Convert and validate numeric fields (price, revenue); flag invalid rows.
4. Impute or drop rows with missing essential fields (product ID, transaction ID) per rules.
5. Resolve inconsistent product and category values using mapping rules.
6. Detect duplicate transaction IDs and keep the most credible record per business rules.
7. Mask PII: replace emails with `***@***.***` pattern and phone numbers with partial masking.
8. Recalculate revenue after deduplication and generate KPI metrics.

## Key Findings

The analysis produced the following results:

| Metric | Value |
|---|---:|
| Raw records | 8,494 |
| Final records after duplicate handling | 8,000 |
| Duplicate transaction IDs identified | 494 |
| Invalid records flagged | 93 |
| Revenue overstatement detected | 74,969,230 |
| Revenue reduction after deduplication | 6.08% |
| Final revenue (post-cleaning) | 1,158,300,920 |
| Top Product | Laptop |
| Top Category | Electronics |
| Top City | Chennai |

## Dashboard Overview (Power BI)

The Power BI report contains the following pages:

1. Executive Summary — overall KPIs and revenue trends
2. Product Performance — sales and revenue by product and category
3. Regional Insights — city-level performance and maps
4. Data Quality & Business Impact — duplicate analysis and revenue adjustments

Use the `PowerBI` folder to locate the report file(s) and data sources.

## Project Structure

```
NeoStats_Assignment/
├── Data/                # Raw input files (Excel)
├── Code/                # ETL scripts and notebooks
│   └── retail_pipeline.py
├── Documentation/       # This project's supporting docs
├── Output/              # Generated CSV outputs and summaries
├── Logs/                # Pipeline logs and validation reports
└── PowerBI/             # Power BI report files and resources
```

### Outputs Generated

- cleaned_retail_data_v2.csv
- kpi_summary_v2.csv
- duplicate_transactions.csv
- invalid_records.csv
- revenue_comparison.csv

These files are written to the `Output` directory by the pipeline.

## Technologies Used

- Python
- Pandas
- OpenPyXL
- Power BI
- Visual Studio Code

## How to Run the Project

Prerequisites:

- Python 3.8+ installed
- Recommended: create a virtual environment

Install dependencies (example):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
pip install pandas openpyxl
```

Run the ETL pipeline:

```powershell
python Code\retail_pipeline.py
```

Expected outputs will be placed in the `Output` folder.

## Notes & Best Practices

- Review and adjust deduplication rules to match business expectations.
- Keep the `Data` folder read-only as the canonical raw source.
- Ensure Power BI sources point to the cleaned CSVs in `Output` for reproducible dashboards.

## Conclusion

This project produced a validated, de-duplicated retail dataset and a set of KPIs and Power BI visuals suitable for business reporting. The deduplication step corrected a material revenue overstatement and improved confidence in downstream analytics.

---

If you need any edits or want me to add a `requirements.txt` or CI script, tell me which format you prefer and I'll add it.
