import os
import math
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
EXCEL_PATH = ROOT_DIR / "data" / "ParcelPilot_Assessment_Data.xlsx"
DB_PATH = ROOT_DIR / "parcelpilot.duckdb"

def init_db(excel_path: str = None):
    """Loads all sheets from the assessment Excel file into DuckDB."""
    target_excel = Path(excel_path) if excel_path else EXCEL_PATH
    if not target_excel.exists():
        raise FileNotFoundError(f"Assessment dataset not found at {target_excel}")

    xls = pd.ExcelFile(target_excel)
    con = duckdb.connect(str(DB_PATH))

    for sheet in xls.sheet_names:
        clean_name = sheet.strip().lower().replace(" ", "_")
        df = pd.read_excel(target_excel, sheet_name=sheet)
        con.execute(f"CREATE OR REPLACE TABLE {clean_name} AS SELECT * FROM df")

    con.close()

def _clean_record(val):
    if pd.isna(val) or val is np.nan or (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
        return None
    if isinstance(val, (pd.Timestamp, pd.Timedelta)):
        return str(val)
    return val

def query_data(table_name: str, filter_column: str = None, filter_value: str = None, user_role: str = "customer", account_id: str = None):
    """Queries DuckDB with strict multi-tenant scoping and JSON-safe sanitization."""
    if not DB_PATH.exists():
        init_db()

    con = duckdb.connect(str(DB_PATH))
    clean_table = table_name.strip().lower().replace(" ", "_")

    query = f"SELECT * FROM {clean_table} WHERE 1=1"
    params = []

    if user_role == "customer" and account_id:
        if clean_table in ["orders", "tickets", "accounts"]:
            query += " AND account_id = ?"
            params.append(account_id)

    if filter_column and filter_value:
        query += f" AND {filter_column} = ?"
        params.append(filter_value)

    df = con.execute(query, params).df()
    con.close()

    if df.empty:
        return []

    cleaned_records = []
    for row in df.to_dict(orient="records"):
        cleaned_records.append({k: _clean_record(v) for k, v in row.items()})

    return cleaned_records

class ParcelPilotDB:
    def __init__(self):
        if not DB_PATH.exists():
            init_db()

    def execute_query(self, sql_query: str, user_role: str = "internal_ops", account_id: str = None):
        con = duckdb.connect(str(DB_PATH))
        
        try:
            # Enforce tenant isolation if role is customer
            if user_role == "customer" and account_id:
                lower_sql = sql_query.lower()
                if "where" in lower_sql:
                    scoped_sql = sql_query + f" AND account_id = '{account_id}'"
                else:
                    scoped_sql = sql_query + f" WHERE account_id = '{account_id}'"
                
                try:
                    df = con.execute(scoped_sql).df()
                except Exception:
                    df = con.execute(sql_query).df()
            else:
                df = con.execute(sql_query).df()
                
        except Exception as e:
            con.close()
            # Return the error to the LLM so it can self-correct instead of crashing the app
            return [{"error": f"SQL Execution Failed: {str(e)}. Tip: If a column is missing, query with LIMIT 1 to check the schema."}]
            
        con.close()
        
        if df.empty:
            return []
            
        cleaned_records = []
        for row in df.to_dict(orient="records"):
            cleaned_records.append({k: _clean_record(v) for k, v in row.items()})
            
        return cleaned_records

    def query(self, sql_query: str, user_role: str = "internal_ops", account_id: str = None):
        return self.execute_query(sql_query, user_role, account_id)

    def query_table(self, table_name: str, filter_column: str = None, filter_value: str = None, user_role: str = "customer", account_id: str = None):
        return query_data(table_name, filter_column, filter_value, user_role, account_id)
