import pandas as pd
from pathlib import Path

# Define the Excel file path relative to this script's parent directory.
excel_path = Path(__file__).resolve().parents[1] / "Data" / "USECASE - Data Engineering.xlsx"

# Verify that the file exists before attempting to read it.
if not excel_path.exists():
    raise FileNotFoundError(f"Excel file not found: {excel_path}")

# Read the workbook using pandas with openpyxl as the engine.
workbook = pd.ExcelFile(excel_path, engine="openpyxl")

print("Excel file:")
print(f"  {excel_path}")
print("\nSheet names:")
for name in workbook.sheet_names:
    print(f"  - {name}")

# Iterate through each sheet and display the requested details.
for sheet_name in workbook.sheet_names:
    print("\n" + "=" * 80)
    print(f"Sheet: {sheet_name}")
    print("=" * 80)

    # Load the sheet into a DataFrame.
    df = workbook.parse(sheet_name)

    # Basic shape information.
    rows, cols = df.shape
    print(f"Rows: {rows}")
    print(f"Columns: {cols}")

    # Column names and data types.
    print("\nColumns and data types:")
    for column, dtype in df.dtypes.items():
        print(f"  - {column}: {dtype}")

    # Missing value counts for each column.
    missing_counts = df.isna().sum()
    print("\nMissing values:")
    for column, count in missing_counts.items():
        print(f"  - {column}: {count}")

    # Duplicate row count.
    duplicate_count = int(df.duplicated().sum())
    print(f"\nDuplicate rows: {duplicate_count}")

    # Show the first 10 rows.
    print("\nFirst 10 rows:")
    if rows == 0:
        print("  (empty sheet)")
    else:
        sample = df.head(10)
        print(sample.to_string(index=False))
