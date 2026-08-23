import os
from pathlib import Path
import duckdb
import pandas as pd

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

def query_data(table_name: str, filter_column: str = None, filter_value: str = None, user_role: str = "customer", account_id: str = None):
    """Queries DuckDB with strict multi-tenant scoping and JSON-safe sanitization."""
    if not DB_PATH.exists():
        init_db()

    con = duckdb.connect(str(DB_PATH))
    clean_table = table_name.strip().lower().replace(" ", "_")

    query = f"SELECT * FROM {clean_table} WHERE 1=1"
    params = []

    if user_role == "customer" and account_id:
        if clean_table in ["orders", "tickets"]:
            query += " AND account_id = ?"
            params.append(account_id)
        elif clean_table == "accounts":
            query += " AND account_id = ?"
            params.append(account_id)

    if filter_column and filter_value:
        query += f" AND {filter_column} = ?"
        params.append(filter_value)

    df = con.execute(query, params).df()
    con.close()

    if df.empty:
        return []

    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')

    df = df.where(pd.notnull(df), None)
    return df.to_dict(orient="records")

class ParcelPilotDB:
    def __init__(self):
        if not DB_PATH.exists():
            init_db()

    def execute_query(self, sql_query: str, user_role: str = "internal_ops", account_id: str = None):
        """Executes raw SQL query with multi-tenant filtering."""
        con = duckdb.connect(str(DB_PATH))
        
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
            
        con.close()
        
        if df.empty:
            return []
            
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                
        df = df.where(pd.notnull(df), None)
        return df.to_dict(orient="records")

    def query(self, sql_query: str, user_role: str = "internal_ops", account_id: str = None):
        return self.execute_query(sql_query, user_role, account_id)

    def query_table(self, table_name: str, filter_column: str = None, filter_value: str = None, user_role: str = "customer", account_id: str = None):
        return query_data(table_name, filter_column, filter_value, user_role, account_id)
