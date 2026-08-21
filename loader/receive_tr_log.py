import os
import duckdb
import pandas as pd
from dotenv import load_dotenv

# Load environment variables (MOTHERDUCK_TOKEN)
load_dotenv()

def main():
    print("==========================================")
    print("      TL Receive MotherDuck Loader        ")
    print("==========================================")

    # Path to the Parquet file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    parquet_path = os.path.join(project_root, 'data', 'tl_receive_raw.parquet')

    if not os.path.exists(parquet_path):
        print(f"WARNING: Parquet file not found at {parquet_path}. Nothing to load.")
        return

    print(f"Reading Parquet file: {parquet_path}")
    df = pd.read_parquet(parquet_path)
    if df.empty:
        print("WARNING: Parquet file is empty. Nothing to load.")
        return

    print("Connecting to MotherDuck...")
    con = duckdb.connect("md:lake")

    # Format data types and columns just to be absolutely safe (already done in scraper, but good to be robust)
    df['ID'] = df['ID'].astype(int)
    df['Quantity'] = df['Quantity'].astype(str)
    df['ReceiveDate'] = pd.to_datetime(df['ReceiveDate'], errors='coerce').dt.date
    df = df[['ID', 'TransferNumber', 'ReceiveBy', 'ItemName', 'Unit', 'Quantity', 'ReceiveDate']]

    # Delete existing IDs to avoid duplication
    unique_ids = df["ID"].unique().tolist()
    if unique_ids:
        print(f"Found {len(unique_ids)} unique IDs to load. Running deduplication...")
        if len(unique_ids) == 1:
            con.execute(f"DELETE FROM tl_receive_data WHERE ID = {unique_ids[0]}")
        else:
            con.execute(f"DELETE FROM tl_receive_data WHERE ID IN {tuple(unique_ids)}")

    # Insert data
    print(f"Inserting {len(df)} rows into MotherDuck table 'tl_receive_data'...")
    con.execute("INSERT INTO tl_receive_data SELECT * FROM df")
    print("SUCCESS: Data successfully saved to MotherDuck!")

if __name__ == "__main__":
    main()
