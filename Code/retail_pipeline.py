import logging
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd


def setup_directories(base_dir: Path) -> Dict[str, Path]:
    """Create required directories and return key paths."""
    output_dir = base_dir / "Output"
    logs_dir = base_dir / "Logs"
    output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    return {
        "output_dir": output_dir,
        "logs_dir": logs_dir,
        "cleaned_data": output_dir / "cleaned_retail_data.csv",
        "kpi_summary": output_dir / "kpi_summary.csv",
        "cleaned_data_v2": output_dir / "cleaned_retail_data_v2.csv",
        "kpi_summary_v2": output_dir / "kpi_summary_v2.csv",
        "duplicate_report": output_dir / "duplicate_transactions.csv",
        "revenue_comparison": output_dir / "revenue_comparison.csv",
        "log_file": logs_dir / "pipeline.log",
    }


def setup_logging(log_file: Path) -> None:
    """Configure logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def read_excel_sheets(file_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Read the three source sheets into pandas DataFrames."""
    logging.info("Reading Excel file: %s", file_path)
    workbook = pd.ExcelFile(file_path, engine="openpyxl")
    product_details = workbook.parse("product_details")
    retail_data1 = workbook.parse("retail_data1")
    retail_data2 = workbook.parse("retail_data2")
    logging.info(
        "Loaded sheets: product_details (%s rows), retail_data1 (%s rows), retail_data2 (%s rows)",
        len(product_details),
        len(retail_data1),
        len(retail_data2),
    )
    return product_details, retail_data1, retail_data2


def merge_retail_data(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """Concatenate retail detail sheets into one DataFrame."""
    logging.info("Merging retail_data1 and retail_data2")
    merged = pd.concat([df1, df2], ignore_index=True)
    logging.info("Merged retail data contains %s rows", len(merged))
    return merged


def standardize_product_names(df: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Standardize product names using the master product table."""
    logging.info("Standardizing product names using product_details")
    product_lookup = (
        products[["product_id", "product_name"]]
        .drop_duplicates(subset=["product_id"])
        .set_index("product_id")["product_name"]
        .to_dict()
    )

    df["product_name"] = df["product_id"].map(product_lookup).fillna(df["product_name"])
    return df


def standardize_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize category labels to canonical values."""
    logging.info("Standardizing category names")
    category_map = {
        "ELEC": "Electronics",
        "electronics": "Electronics",
        "electronics ": "Electronics",
        "FURN": "Furniture",
        "HOME": "Home Appliances",
        "home appliances": "Home Appliances",
        "CLOTH": "Clothing",
    }

    df["category"] = df["category"].astype(str).str.strip()
    df["category"] = df["category"].replace(category_map)
    df["category"] = df["category"].str.title().replace(
        {
            "Electronics": "Electronics",
            "Furniture": "Furniture",
            "Home Appliances": "Home Appliances",
            "Clothing": "Clothing",
        }
    )
    return df


def parse_transaction_date(df: pd.DataFrame) -> pd.DataFrame:
    """Parse transaction_date into a standard datetime column."""
    logging.info("Converting transaction_date to datetime")
    df["transaction_date"] = pd.to_datetime(
    df["transaction_date"],
    errors="coerce"
)
    invalid_dates = df["transaction_date"].isna().sum()
    logging.info("Found %s invalid or unparseable transaction_date values", invalid_dates)
    return df


def fill_missing_prices(df: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Fill missing price values using the product master table."""
    logging.info("Filling missing prices from product_details")
    price_lookup = products.set_index("product_id")["price"].to_dict()
    missing_before = df["price"].isna().sum()
    df["price"] = df.apply(
        lambda row: price_lookup.get(row["product_id"]) if pd.isna(row["price"]) else row["price"],
        axis=1,
    )
    missing_after = df["price"].isna().sum()
    logging.info(
        "Missing price values before=%s, after=%s", missing_before, missing_after
    )
    return df


def duplicate_transaction_report(df: pd.DataFrame) -> pd.DataFrame:
    """Report duplicate transaction IDs and return a separate DataFrame."""
    logging.info("Checking for duplicate transaction IDs")
    duplicate_report = (
        df.groupby("transaction_id")
        .filter(lambda group: len(group) > 1)
        .sort_values("transaction_id")
        .reset_index(drop=True)
    )
    logging.info("Found %s duplicate transaction_id rows", len(duplicate_report))
    return duplicate_report


def resolve_duplicate_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Apply business rules to resolve duplicate transaction IDs."""
    logging.info("Resolving duplicate transaction IDs by business rule")

    def keep_record(group: pd.DataFrame) -> pd.DataFrame:
        successful = group[group["payment_status"] == "successful"]
        if not successful.empty:
            chosen = successful.iloc[[0]].copy()
        else:
            chosen = group.iloc[[0]].copy()
        chosen["transaction_id"] = group.name
        return chosen

    resolved = (
        df.groupby("transaction_id", group_keys=False)
        .apply(keep_record)
    )

    if "transaction_id" not in resolved.columns and resolved.index.name == "transaction_id":
        resolved = resolved.reset_index()

    resolved = resolved.reset_index(drop=True)
    removed = len(df) - len(resolved)
    logging.info(
        "Duplicate resolution removed %s rows; %s rows remain after deduplication",
        removed,
        len(resolved),
    )
    return resolved


def revenue_comparison_report(before_revenue: float, after_revenue: float) -> pd.DataFrame:
    """Build a revenue comparison report before and after duplicate handling."""
    difference = after_revenue - before_revenue
    percentage_difference = (
        difference / before_revenue * 100 if before_revenue != 0 else 0.0
    )
    return pd.DataFrame(
        [
            {"metric": "revenue_before_duplicate_handling", "value": before_revenue},
            {"metric": "revenue_after_duplicate_handling", "value": after_revenue},
            {"metric": "revenue_difference", "value": difference},
            {"metric": "revenue_percentage_difference", "value": percentage_difference},
        ]
    )


def validate_data(df: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Validate core fields and log invalid records."""
    logging.info("Validating retail data")
    valid_product_ids = set(products["product_id"].unique())

    validations = pd.DataFrame(
        {
            "transaction_id": df["transaction_id"],
            "is_valid_quantity": df["quantity"] > 0,
            "is_valid_price": df["price"] > 0,
            "product_id_exists": df["product_id"].isin(valid_product_ids),
            "transaction_id_exists": df["transaction_id"].notna(),
        }
    )

    invalid_rows = df[
        (~validations["is_valid_quantity"])
        | (~validations["is_valid_price"])
        | (~validations["product_id_exists"])
        | (~validations["transaction_id_exists"])
    ]

    logging.info("Validation summary:")
    logging.info("  Invalid quantity: %s", (~validations["is_valid_quantity"]).sum())
    logging.info("  Invalid price: %s", (~validations["is_valid_price"]).sum())
    logging.info("  Missing product_id match: %s", (~validations["product_id_exists"]).sum())
    logging.info("  Missing transaction_id: %s", (~validations["transaction_id_exists"]).sum())

    if not invalid_rows.empty:
        logging.warning("Found %s invalid rows", len(invalid_rows))
    return invalid_rows


def mask_email(email: str) -> str:
    """Mask an email address while preserving the domain."""
    if not isinstance(email, str) or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    masked_local = local[:2] + "****" if len(local) > 2 else local + "****"
    return f"{masked_local}@{domain}"


def mask_phone(phone) -> str:
    """Mask a phone number while preserving the first three and last three digits."""
    phone_str = str(phone).strip()
    if len(phone_str) < 7 or not phone_str.isdigit():
        return phone_str
    return f"{phone_str[:3]}****{phone_str[-3:]}"


def mask_pii(df: pd.DataFrame) -> pd.DataFrame:
    """Mask PII columns in the retail dataset."""
    logging.info("Masking PII columns")
    df["email"] = df["email"].apply(mask_email)
    df["phone"] = df["phone"].apply(mask_phone)
    return df


def create_revenue_column(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate revenue for each transaction record."""
    logging.info("Creating Revenue column")
    df["revenue"] = df["price"] * df["quantity"] * (1 - df["discount"])
    return df


def generate_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Generate an aggregate KPI summary report."""
    logging.info("Generating KPI summary")
    total_revenue = df["revenue"].sum()
    total_transactions = df["transaction_id"].nunique()
    total_customers = df["customer_id"].nunique()
    average_order_value = df.groupby("transaction_id")["revenue"].sum().mean()
    top_product = (
        df.groupby("product_name")["revenue"].sum().idxmax()
        if not df.empty
        else None
    )
    top_category = (
        df.groupby("category")["revenue"].sum().idxmax() if not df.empty else None
    )
    top_city = df.groupby("city")["revenue"].sum().idxmax() if not df.empty else None

    kpis = {
        "total_revenue": total_revenue,
        "total_transactions": total_transactions,
        "total_customers": total_customers,
        "average_order_value": average_order_value,
        "top_product": top_product,
        "top_category": top_category,
        "top_city": top_city,
    }

    revenue_by_category = df.groupby("category")["revenue"].sum().reset_index()
    revenue_by_city = df.groupby("city")["revenue"].sum().reset_index()

    kpi_summary = pd.DataFrame(
        [
            {"metric": "total_revenue", "value": total_revenue},
            {"metric": "total_transactions", "value": total_transactions},
            {"metric": "total_customers", "value": total_customers},
            {"metric": "average_order_value", "value": average_order_value},
            {"metric": "top_product", "value": top_product},
            {"metric": "top_category", "value": top_category},
            {"metric": "top_city", "value": top_city},
        ]
    )

    revenue_by_category["metric"] = "revenue_by_category"
    revenue_by_category = revenue_by_category.rename(columns={"revenue": "value"})
    revenue_by_city["metric"] = "revenue_by_city"
    revenue_by_city = revenue_by_city.rename(columns={"revenue": "value"})

    return pd.concat([kpi_summary, revenue_by_category, revenue_by_city], ignore_index=True)


def export_outputs(
    cleaned_df: pd.DataFrame,
    kpi_df: pd.DataFrame,
    duplicate_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
    paths: Dict[str, Path],
) -> None:
    """Write cleaned dataset, KPI summary, duplicate report, and comparison report to CSV."""
    logging.info("Exporting cleaned retail data to %s", paths["cleaned_data"])
    cleaned_df.to_csv(paths["cleaned_data"], index=False)
    logging.info("Exporting KPI summary to %s", paths["kpi_summary"])
    kpi_df.to_csv(paths["kpi_summary"], index=False)
    logging.info("Exporting duplicate transaction report to %s", paths["duplicate_report"])
    duplicate_df.to_csv(paths["duplicate_report"], index=False)
    logging.info("Exporting revenue comparison report to %s", paths["revenue_comparison"])
    comparison_df.to_csv(paths["revenue_comparison"], index=False)


def export_v2_outputs(
    cleaned_df: pd.DataFrame,
    kpi_df: pd.DataFrame,
    paths: Dict[str, Path],
) -> None:
    """Export version 2 cleaned dataset and KPI summary after duplicate handling."""
    logging.info("Exporting cleaned retail data v2 to %s", paths["cleaned_data_v2"])
    cleaned_df.to_csv(paths["cleaned_data_v2"], index=False)
    logging.info("Exporting KPI summary v2 to %s", paths["kpi_summary_v2"])
    kpi_df.to_csv(paths["kpi_summary_v2"], index=False)


def main() -> None:
    """Main pipeline orchestration."""
    base_dir = Path(__file__).resolve().parents[1]
    paths = setup_directories(base_dir)
    setup_logging(paths["log_file"])

    source_file = base_dir / "Data" / "USECASE - Data Engineering.xlsx"
    products, retail1, retail2 = read_excel_sheets(source_file)

    retail = merge_retail_data(retail1, retail2)
    retail = standardize_product_names(retail, products)
    retail = standardize_categories(retail)
    retail = parse_transaction_date(retail)
    retail = fill_missing_prices(retail, products)

    duplicate_report = duplicate_transaction_report(retail)
    invalid_rows = validate_data(retail, products)
    if not invalid_rows.empty:
        invalid_path = paths["output_dir"] / "invalid_records.csv"
        invalid_rows.to_csv(invalid_path, index=False)
        logging.warning("Exported invalid records to %s", invalid_path)

    # Write the original cleaned output prior to duplicate-resolution business rule
    retail_pre_dedup = mask_pii(retail.copy())
    retail_pre_dedup = create_revenue_column(retail_pre_dedup)
    kpi_summary = generate_kpis(retail_pre_dedup)
    export_outputs(retail_pre_dedup, kpi_summary, duplicate_report, pd.DataFrame(), paths)

    # Apply duplicate transaction business rule and recalculate KPIs
    retail_dedup = resolve_duplicate_transactions(retail)
    retail_dedup = mask_pii(retail_dedup)
    retail_dedup = create_revenue_column(retail_dedup)
    kpi_summary_v2 = generate_kpis(retail_dedup)
    export_v2_outputs(retail_dedup, kpi_summary_v2, paths)

    revenue_before = retail_pre_dedup["revenue"].sum()
    revenue_after = retail_dedup["revenue"].sum()
    comparison_df = revenue_comparison_report(revenue_before, revenue_after)
    logging.info(
        "Revenue before duplicate handling: %s, after: %s, difference: %s",
        revenue_before,
        revenue_after,
        revenue_after - revenue_before,
    )
    comparison_df.to_csv(paths["revenue_comparison"], index=False)

    logging.info("Retail pipeline completed successfully")


if __name__ == "__main__":
    main()
