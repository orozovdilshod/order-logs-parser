"""
Order Logs Parser & Aggregator
Parses orders.csv, validates records, extracts year-month,
aggregates total monthly revenue per customer, and prints results sorted descending.
"""

import sys
import os
from datetime import datetime

# Optional pandas import; falls back seamlessly to standard library csv if pandas is unavailable
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    import csv


def parse_date(date_str):
    """
    Attempts to parse multiple date/timestamp formats into a datetime object.
    Returns datetime or raises ValueError if format is unrecognized.
    """
    date_str = date_str.strip()
    # Try ISO formats and common variations
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%m/%d/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    # Attempt Python's built-in isoformat parser as fallback
    try:
        return datetime.fromisoformat(date_str)
    except Exception:
        raise ValueError(f"Unrecognized date format: '{date_str}'")


def process_orders_with_pandas(csv_path):
    """
    Implementation using pandas DataFrame operations.
    """
    df_raw = pd.read_csv(csv_path, dtype=str)
    required_cols = ["order_id", "customer_id", "amount", "created_at"]
    missing_cols = [c for c in required_cols if c not in df_raw.columns]
    if missing_cols:
        raise ValueError(f"Missing required CSV columns: {missing_cols}")

    valid_records = []
    print("\n--- Validating Rows ---")
    for idx, row in df_raw.iterrows():
        row_num = idx + 2  # Accounting for header line (1-indexed)
        order_id = str(row.get("order_id", "")).strip() if pd.notna(row.get("order_id")) else ""
        customer_id = str(row.get("customer_id", "")).strip() if pd.notna(row.get("customer_id")) else ""
        amount_raw = row.get("amount")
        created_at_raw = str(row.get("created_at", "")).strip() if pd.notna(row.get("created_at")) else ""

        # Validate order_id
        if not order_id or order_id.lower() == "nan":
            print(f"[SKIPPED] Line {row_num}: Missing or empty 'order_id'")
            continue

        # Validate customer_id
        if not customer_id or customer_id.lower() == "nan":
            print(f"[SKIPPED] Line {row_num} (order_id: {order_id}): Missing or empty 'customer_id'")
            continue

        # Validate amount presence and numeric value
        if pd.isna(amount_raw) or str(amount_raw).strip() == "" or str(amount_raw).strip().lower() == "nan":
            print(f"[SKIPPED] Line {row_num} (order_id: {order_id}): Missing 'amount'")
            continue

        try:
            amount_val = float(str(amount_raw).strip())
            if amount_val < 0:
                print(f"[SKIPPED] Line {row_num} (order_id: {order_id}): Invalid negative amount ({amount_val})")
                continue
        except (ValueError, TypeError):
            print(f"[SKIPPED] Line {row_num} (order_id: {order_id}): Invalid numeric amount '{amount_raw}'")
            continue

        # Validate created_at
        if not created_at_raw or created_at_raw.lower() == "nan":
            print(f"[SKIPPED] Line {row_num} (order_id: {order_id}): Missing 'created_at'")
            continue

        try:
            dt = parse_date(created_at_raw)
            month_str = dt.strftime("%Y-%m")
        except ValueError as e:
            print(f"[SKIPPED] Line {row_num} (order_id: {order_id}): {e}")
            continue

        valid_records.append({
            "order_id": order_id,
            "customer_id": customer_id,
            "amount": amount_val,
            "month": month_str,
        })

    if not valid_records:
        print("\nNo valid records found.")
        return

    df_valid = pd.DataFrame(valid_records)
    print(f"\n[Validation Summary] Valid rows: {len(df_valid)} | Skipped rows: {len(df_raw) - len(df_valid)}")

    # Aggregate: group by customer_id and month, sum amount
    agg_df = (
        df_valid.groupby(["customer_id", "month"], as_index=False)["amount"]
        .sum()
        .rename(columns={"amount": "total_revenue"})
    )
    agg_df["total_revenue"] = agg_df["total_revenue"].round(2)

    # Sort descending by total_revenue
    agg_df = agg_df.sort_values(by="total_revenue", ascending=False).reset_index(drop=True)

    print("\n--- Aggregated Revenue by Customer and Month (Sorted Descending) ---")
    print(f"{'Customer ID':<15} {'Month':<10} {'Total Revenue ($)':>18}")
    print("-" * 46)
    for _, r in agg_df.iterrows():
        print(f"{r['customer_id']:<15} {r['month']:<10} {r['total_revenue']:>18.2f}")

    return agg_df


def process_orders_with_csv(csv_path):
    """
    Standard library csv implementation for environments without external packages.
    """
    import csv
    from collections import defaultdict

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        required_cols = ["order_id", "customer_id", "amount", "created_at"]
        missing_cols = [c for c in required_cols if c not in fieldnames]
        if missing_cols:
            raise ValueError(f"Missing required CSV columns: {missing_cols}")

        valid_count = 0
        skipped_count = 0
        monthly_revenue = defaultdict(float)

        print("\n--- Validating Rows ---")
        for line_num, row in enumerate(reader, start=2):
            order_id = (row.get("order_id") or "").strip()
            customer_id = (row.get("customer_id") or "").strip()
            amount_raw = (row.get("amount") or "").strip()
            created_at_raw = (row.get("created_at") or "").strip()

            if not order_id:
                print(f"[SKIPPED] Line {line_num}: Missing or empty 'order_id'")
                skipped_count += 1
                continue

            if not customer_id:
                print(f"[SKIPPED] Line {line_num} (order_id: {order_id}): Missing or empty 'customer_id'")
                skipped_count += 1
                continue

            if not amount_raw:
                print(f"[SKIPPED] Line {line_num} (order_id: {order_id}): Missing 'amount'")
                skipped_count += 1
                continue

            try:
                amount_val = float(amount_raw)
                if amount_val < 0:
                    print(f"[SKIPPED] Line {line_num} (order_id: {order_id}): Invalid negative amount ({amount_val})")
                    skipped_count += 1
                    continue
            except ValueError:
                print(f"[SKIPPED] Line {line_num} (order_id: {order_id}): Invalid numeric amount '{amount_raw}'")
                skipped_count += 1
                continue

            if not created_at_raw:
                print(f"[SKIPPED] Line {line_num} (order_id: {order_id}): Missing 'created_at'")
                skipped_count += 1
                continue

            try:
                dt = parse_date(created_at_raw)
                month_str = dt.strftime("%Y-%m")
            except ValueError as e:
                print(f"[SKIPPED] Line {line_num} (order_id: {order_id}): {e}")
                skipped_count += 1
                continue

            # Accumulate revenue
            monthly_revenue[(customer_id, month_str)] += amount_val
            valid_count += 1

    print(f"\n[Validation Summary] Valid rows: {valid_count} | Skipped rows: {skipped_count}")

    if not monthly_revenue:
        print("\nNo valid records found.")
        return

    # Sort descending by total_revenue
    sorted_results = sorted(
        [
            {"customer_id": cid, "month": m, "total_revenue": round(rev, 2)}
            for (cid, m), rev in monthly_revenue.items()
        ],
        key=lambda x: x["total_revenue"],
        reverse=True,
    )

    print("\n--- Aggregated Revenue by Customer and Month (Sorted Descending) ---")
    print(f"{'Customer ID':<15} {'Month':<10} {'Total Revenue ($)':>18}")
    print("-" * 46)
    for r in sorted_results:
        print(f"{r['customer_id']:<15} {r['month']:<10} {r['total_revenue']:>18.2f}")

    return sorted_results


def main():
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "orders.csv"

    if not os.path.exists(csv_file):
        print(f"Error: File '{csv_file}' was not found.")
        sys.exit(1)

    print(f"Processing order logs from: {csv_file}")
    if HAS_PANDAS:
        print("Using engine: pandas")
        process_orders_with_pandas(csv_file)
    else:
        print("Using engine: Python standard csv (pandas not installed)")
        process_orders_with_csv(csv_file)


if __name__ == "__main__":
    main()
