import pandas as pd
import numpy as np
from pathlib import Path

# -----------------------------
# Project paths
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

np.random.seed(42)

# -----------------------------
# Step 1: Generate platform_transactions
# -----------------------------
def create_platform_transactions():
    n = 30
    platform_dates = pd.date_range("2026-03-01", "2026-03-29", periods=n).floor("D")

    platform = pd.DataFrame({
        "transaction_id": [f"TXN{1000+i}" for i in range(n)],
        "platform_date": platform_dates,
        "amount_raw": np.random.choice(
            [199.995, 249.995, 499.995, 99.995, 149.995, 299.995],
            size=n
        ),
        "currency": "INR",
        "type": "payment"
    })

    # Bank settles in 1-2 days
    platform["settlement_date"] = platform["platform_date"] + pd.to_timedelta(
        np.random.choice([1, 2], size=n),
        unit="D"
    )

    platform["amount"] = platform["amount_raw"].round(2)
    platform["settlement_month"] = platform["settlement_date"].dt.to_period("M").astype(str)

    return platform

# -----------------------------
# Step 2: Generate bank_settlements
# -----------------------------
def create_bank_settlements(platform):
    bank = platform[[
        "transaction_id", "settlement_date", "amount_raw", "currency", "type"
    ]].copy()

    bank.rename(columns={"settlement_date": "bank_date"}, inplace=True)
    bank["amount"] = bank["amount_raw"].round(2)

    # GAP 1: transaction settles in following month
    late_txn_id = platform.iloc[-1]["transaction_id"]
    bank.loc[bank["transaction_id"] == late_txn_id, "bank_date"] = pd.Timestamp("2026-04-01")

    # GAP 2: rounding difference visible in sums
    rounding_ids = platform.iloc[0:3]["transaction_id"].tolist()
    bank.loc[bank["transaction_id"].isin(rounding_ids), "amount_raw"] = (
        bank.loc[bank["transaction_id"].isin(rounding_ids), "amount_raw"] - 0.004
    )
    bank["amount"] = bank["amount_raw"].round(2)

    # GAP 3: duplicate entry in bank dataset
    duplicate_row = bank.iloc[[5]].copy()
    bank = pd.concat([bank, duplicate_row], ignore_index=True)

    # GAP 4: refund with no matching original transaction
    refund_row = pd.DataFrame([{
        "transaction_id": "RFND9999",
        "bank_date": pd.Timestamp("2026-03-20"),
        "amount_raw": -149.99,
        "currency": "INR",
        "type": "refund",
        "amount": -149.99
    }])
    bank = pd.concat([bank, refund_row], ignore_index=True)

    bank["settlement_month"] = pd.to_datetime(bank["bank_date"]).dt.to_period("M").astype(str)

    return bank

# -----------------------------
# Step 3: Save source tables
# -----------------------------
def save_source_data(platform, bank):
    platform.to_csv(DATA_DIR / "platform_transactions.csv", index=False)
    bank.to_csv(DATA_DIR / "bank_settlements.csv", index=False)

# -----------------------------
# Step 4: Reconciliation logic
# -----------------------------
def reconcile():
    platform = pd.read_csv(DATA_DIR / "platform_transactions.csv", parse_dates=["platform_date", "settlement_date"])
    bank = pd.read_csv(DATA_DIR / "bank_settlements.csv", parse_dates=["bank_date"])

    platform["settlement_month"] = platform["settlement_date"].dt.to_period("M").astype(str)
    bank["settlement_month"] = bank["bank_date"].dt.to_period("M").astype(str)

    # Monthly totals
    platform_monthly = (
        platform.groupby("settlement_month", as_index=False)
        .agg(
            platform_total_raw=("amount_raw", "sum"),
            platform_total_rounded=("amount", "sum"),
            platform_count=("transaction_id", "count")
        )
    )

    bank_monthly = (
        bank.groupby("settlement_month", as_index=False)
        .agg(
            bank_total_raw=("amount_raw", "sum"),
            bank_total_rounded=("amount", "sum"),
            bank_count=("transaction_id", "count")
        )
    )

    monthly_summary = platform_monthly.merge(
        bank_monthly, on="settlement_month", how="outer"
    ).fillna(0)

    monthly_summary["raw_diff"] = (
        monthly_summary["platform_total_raw"] - monthly_summary["bank_total_raw"]
    ).round(4)

    monthly_summary["rounded_diff"] = (
        monthly_summary["platform_total_rounded"] - monthly_summary["bank_total_rounded"]
    ).round(2)

    # Duplicate in bank
    duplicate_in_bank = (
        bank.groupby("transaction_id", as_index=False)
        .size()
        .query("size > 1")
    )

    # Refunds with no original transaction in platform
    platform_ids = set(platform["transaction_id"])
    orphan_refunds = bank[
        (bank["type"] == "refund") & (~bank["transaction_id"].isin(platform_ids))
    ][["transaction_id", "bank_date", "amount", "type"]]

    # Platform transactions missing in bank
    bank_unique_ids = set(bank["transaction_id"])
    missing_in_bank = platform[~platform["transaction_id"].isin(bank_unique_ids)][
        ["transaction_id", "platform_date", "settlement_date", "amount", "type"]
    ]

    # Extra ids in bank
    extra_in_bank = bank[~bank["transaction_id"].isin(set(platform["transaction_id"]))][
        ["transaction_id", "bank_date", "amount", "type"]
    ]

    # Save outputs
    monthly_summary.to_csv(OUTPUT_DIR / "monthly_summary.csv", index=False)
    duplicate_in_bank.to_csv(OUTPUT_DIR / "duplicate_in_bank.csv", index=False)
    orphan_refunds.to_csv(OUTPUT_DIR / "orphan_refunds.csv", index=False)
    missing_in_bank.to_csv(OUTPUT_DIR / "missing_in_bank.csv", index=False)
    extra_in_bank.to_csv(OUTPUT_DIR / "extra_in_bank.csv", index=False)

    # Print quick summary
    print("\n=== FILES GENERATED ===")
    print(DATA_DIR / "platform_transactions.csv")
    print(DATA_DIR / "bank_settlements.csv")
    print(OUTPUT_DIR / "monthly_summary.csv")
    print(OUTPUT_DIR / "duplicate_in_bank.csv")
    print(OUTPUT_DIR / "orphan_refunds.csv")
    print(OUTPUT_DIR / "missing_in_bank.csv")
    print(OUTPUT_DIR / "extra_in_bank.csv")

    print("\n=== MONTHLY SUMMARY ===")
    print(monthly_summary.to_string(index=False))

    print("\n=== DUPLICATE IN BANK ===")
    print(duplicate_in_bank.to_string(index=False))

    print("\n=== ORPHAN REFUNDS ===")
    print(orphan_refunds.to_string(index=False))

# -----------------------------
# Run everything
# -----------------------------
if __name__ == "__main__":
    platform = create_platform_transactions()
    bank = create_bank_settlements(platform)
    save_source_data(platform, bank)
    reconcile()