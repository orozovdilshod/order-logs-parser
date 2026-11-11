# Order Logs Parser & Aggregator

A Python data engineering utility to parse e-commerce order logs, validate transaction records, handle corrupted and malformed data, and aggregate monthly revenue per customer.

---

## 📌 Project Description

This project processes transaction logs from `orders.csv`. It cleans and validates the dataset, skips invalid rows with clear logging, extracts year-month periods, aggregates total revenue per customer per month, and displays the final aggregated results sorted in descending order of revenue.

### Expected Input Format (`orders.csv`):
| Column Name | Type | Description |
| :--- | :--- | :--- |
| `order_id` | String / Integer | Unique order identifier |
| `customer_id` | String / Integer | Unique customer identifier |
| `amount` | Float / Numeric | Transaction amount (must be positive numeric) |
| `created_at` | Date / Timestamp | Order creation timestamp (e.g. `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS`) |

### Validation Rules:
Rows are automatically **skipped and logged** if:
1. `order_id` or `customer_id` is missing or empty.
2. `amount` is missing, empty, non-numeric (e.g. text), or negative (`amount < 0`).
3. `created_at` is missing, empty, or cannot be parsed into a valid date/timestamp format.

---

## ⚙️ Requirements

- **Python**: 3.8+
- **Libraries**:
  - `pandas` (recommended for vectorized DataFrame transformations)
  - *Note:* `solution.py` includes a built-in fallback using Python's standard `csv` module, so it can run out of the box even without external dependencies.

---

## 🚀 Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/orozovdilshod/order-logs-parser.git
   cd order-logs-parser
   ```

2. **Install dependencies (Optional)**:
   ```bash
   pip install pandas
   ```

---

## 💻 Usage

Run the script using the default `orders.csv` in the root folder:

```bash
python solution.py
```

Or pass a custom CSV file path as a command-line argument:

```bash
python solution.py path/to/custom_orders.csv
```

---

## 📊 Sample Execution & Expected Output

Given the sample `orders.csv`:
```csv
order_id,customer_id,amount,created_at
101,C101,150.00,2026-10-01
102,C102,200.50,2026-10-05
103,C101,50.00,2026-10-12
104,C103,invalid_amount,2026-10-15
105,C102,,2026-10-20
106,C101,300.00,2026-11-01
107,C103,120.00,invalid_date
108,,75.00,2026-10-10
109,C104,-45.00,2026-10-11
,C105,80.00,2026-10-12
110,C102,99.50,2026-11-04 14:30:00
111,C102,150.00,2026-11-15
```

Running `python solution.py` outputs:
```text
Processing order logs from: orders.csv
Using engine: pandas

--- Validating Rows ---
[SKIPPED] Line 5 (order_id: 104): Invalid numeric amount 'invalid_amount'
[SKIPPED] Line 6 (order_id: 105): Missing 'amount'
[SKIPPED] Line 8 (order_id: 107): Unrecognized date format: 'invalid_date'
[SKIPPED] Line 9 (order_id: 108): Missing or empty 'customer_id'
[SKIPPED] Line 10 (order_id: 109): Invalid negative amount (-45.0)
[SKIPPED] Line 11: Missing or empty 'order_id'

[Validation Summary] Valid rows: 6 | Skipped rows: 6

--- Aggregated Revenue by Customer and Month (Sorted Descending) ---
Customer ID     Month      Total Revenue ($)
----------------------------------------------
C101            2026-11               300.00
C102            2026-11               249.50
C101            2026-10               200.00
C102            2026-10               200.50
```
