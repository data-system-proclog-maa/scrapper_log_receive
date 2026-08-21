import os
import duckdb
from dotenv import load_dotenv

# Load environment variables (such as MOTHERDUCK_TOKEN)
load_dotenv()

def main():
    print("==========================================")
    print("      TR Entry List MotherDuck Loader     ")
    print("==========================================")

    # Path to the Parquet file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    parquet_path = os.path.join(project_root, 'data', 'tr_entry_raw.parquet')

    if not os.path.exists(parquet_path):
        print(f"WARNING: Parquet file not found at {parquet_path}. Nothing to load.")
        return

    print("Connecting to MotherDuck...")
    con = duckdb.connect("md:lake")

    # Verify if parquet file contains data using DuckDB
    row_count = con.execute("SELECT COUNT(*) FROM read_parquet(?)", [parquet_path]).fetchone()[0]
    if row_count == 0:
        print("WARNING: Parquet file is empty. Nothing to load.")
        return

    print(f"Found {row_count} rows in parquet file. Processing with DuckDB SQL...")

    # Create target table if it does not exist
    con.execute("""
    CREATE TABLE IF NOT EXISTS tr_entry_list (
        "ID" INTEGER,
        "TransferNumber" VARCHAR,
        "Department" VARCHAR,
        "PO Number" VARCHAR,
        "Item Description" VARCHAR,
        "UoM" VARCHAR,
        "ETA" DATE,
        "Qty Shipped" VARCHAR,
        "Qty Received" VARCHAR,
        "Additional Item" BOOLEAN
    );
    """)

    # Stage, format data types, and filter out rows where Item Description or PO Number is empty
    con.execute("""
    CREATE OR REPLACE TEMP TABLE stage_tr_entry AS
    SELECT 
        TRY_CAST("ID" AS INTEGER) AS "ID",
        CAST("TransferNumber" AS VARCHAR) AS "TransferNumber",
        CAST("Department" AS VARCHAR) AS "Department",
        CAST("PO Number" AS VARCHAR) AS "PO Number",
        CAST("Item Description" AS VARCHAR) AS "Item Description",
        CAST("UoM" AS VARCHAR) AS "UoM",
        TRY_CAST("ETA" AS DATE) AS "ETA",
        CAST("Qty Shipped" AS VARCHAR) AS "Qty Shipped",
        CAST("Qty Received" AS VARCHAR) AS "Qty Received",
        CAST("Additional Item" AS BOOLEAN) AS "Additional Item"
    FROM read_parquet(?)
    WHERE TRIM(COALESCE(CAST("Item Description" AS VARCHAR), '')) != ''
      AND TRIM(COALESCE(CAST("PO Number" AS VARCHAR), '')) != '';
    """, [parquet_path])

    staged_count = con.execute("SELECT COUNT(*) FROM stage_tr_entry").fetchone()[0]

    # Run deduplication using DuckDB
    unique_ids_count = con.execute("SELECT COUNT(DISTINCT ID) FROM stage_tr_entry").fetchone()[0]
    print(f"Running deduplication for {unique_ids_count} unique IDs...")
    con.execute("""
    DELETE FROM tr_entry_list 
    WHERE ID IN (SELECT DISTINCT ID FROM stage_tr_entry);
    """)

    # Insert formatted stage data into MotherDuck table
    print(f"Inserting {staged_count} valid rows into MotherDuck table 'tr_entry_list'...")
    con.execute("INSERT INTO tr_entry_list SELECT * FROM stage_tr_entry")
    print("SUCCESS: Data successfully processed and saved to MotherDuck!")

if __name__ == "__main__":
    main()