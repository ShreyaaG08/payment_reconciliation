# Payment Reconciliation Project

## Overview
This project simulates a payment reconciliation problem for a payments company.

The company records every customer payment instantly on its platform, while the bank settles the money 1–2 days later. At month end, both records should match. This project generates synthetic data and identifies why they do not match.

## Problem Statement
A payments company's books do not balance at month end.

They know:
- Every transaction processed by their platform
- Every settlement amount received from the bank

These two should match, but they do not.

The project finds the mismatch reasons and shows where the gaps are.

## Gap Types Included
This project intentionally creates these gap types:
1. A transaction that settled in the following month
2. A rounding difference that appears only when totals are summed
3. A duplicate entry in one dataset
4. A refund with no matching original transaction

## Assumptions
- All transactions are in INR
- The platform records payments instantly
- The bank settles payments 1–2 days later
- Refunds appear as negative amounts
- Month-end reconciliation is based on settlement month
- Amounts may have hidden decimal precision before final rounding

## Project Structure
```text
payment_reconciliation/
│
├── main.py
├── requirements.txt
├── README.md
├── data/
│   ├── platform_transactions.csv
│   └── bank_settlements.csv
└── output/
    ├── monthly_summary.csv
    ├── duplicate_in_bank.csv
    ├── orphan_refunds.csv
    ├── missing_in_bank.csv
    └── extra_in_bank.csv
```

## Installation
Install dependencies using:

```bash
pip install -r requirements.txt
```

## Run the project
Run:

```bash
python main.py
```

## Input Files Generated
After running the script, these source files will be created automatically inside `data/`:

- `platform_transactions.csv`
- `bank_settlements.csv`

## Output Files Generated
After reconciliation, these result files will be created inside `output/`:

- `monthly_summary.csv`
- `duplicate_in_bank.csv`
- `orphan_refunds.csv`
- `missing_in_bank.csv`
- `extra_in_bank.csv`

## Dataset Description

### platform_transactions.csv
Contains payment records from the internal platform.

Columns:
- `transaction_id`
- `platform_date`
- `amount_raw`
- `currency`
- `type`
- `settlement_date`
- `amount`
- `settlement_month`

### bank_settlements.csv
Contains settlement records from the bank.

Columns:
- `transaction_id`
- `bank_date`
- `amount_raw`
- `currency`
- `type`
- `amount`
- `settlement_month`

## Reconciliation Logic
The script performs:
- Monthly total comparison
- Duplicate transaction detection
- Orphan refund detection
- Missing transaction detection
- Extra bank record detection
- Rounding difference analysis

## Expected Result
The monthly totals will not match because the dataset intentionally contains reconciliation gaps. The script identifies the exact reason for each mismatch and saves separate CSV reports for review.