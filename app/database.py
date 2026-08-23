import os
import duckdb
import pandas as pd

DB_PATH = "parcelpilot.duckdb"

def init_db(excel_path: str = "data/ParcelPilot_Assessment_Data.xlsx"):
    """Loads all sheets from the assessment Excel file into DuckDB."""
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Assessment dataset not found at {excel_path}")

    xls = pd.ExcelFile(excel_path)
    con = duckdb.connect(DB_PATH)

    for sheet in xls.sheet_names:
        clean_name = sheet.strip().lower().replace(" ", "_")
        df = pd.read_excel(excel_path, sheet_name=sheet)
        con.execute(f"CREATE OR REPLACE TABLE {clean_name} AS SELECT * FROM df")

    con.close()

def query_data(table_name: str, filter_column: str = None, filter_value: str = None, user_role: str = "customer", account_id: str = None):
    """Queries DuckDB with strict multi-tenant scoping and JSON-safe sanitization."""
    if not os.path.exists(DB_PATH):
        init_db()

    con = duckdb.connect(DB_PATH)
    clean_table = table_name.strip().lower().replace(" ", "_")

    query = f"SELECT * FROM {clean_table} WHERE 1=1"
    params = []

    # Enforce data tenancy for customer role
    if user_role == "customer" and account_id:
        if clean_table in ["orders", "tickets"]:
            query += " AND account_id = ?"
            params.append(account_id)
        elif clean_table == "accounts":
            query += " AND account_id = ?"
            params.append(account_id)

    # Optional specific column filtering
    if filter_column and filter_value:
        query += f" AND {filter_column} = ?"
        params.append(filter_value)

    df = con.execute(query, params).df()
    con.close()

    if df.empty:
        return []

    # Sanitize timestamps and replace NaN/NaT with None for clean JSON serialization
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')

    df = df.where(pd.notnull(df), None)
    return df.to_dict(orient="records")