import sys
import os

# Ensure current directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from receive_log import login_to_cps_mobile, scrape_po_receive
from playwright.sync_api import sync_playwright

def main():
    print("==========================================")
    print("        PO Receive Scraper Runner         ")
    print("==========================================")
    
    import argparse
    import datetime

    parser = argparse.ArgumentParser(description="PO Receive Scraper Runner")
    parser.add_argument("--start", type=int, help="Start ID (default: 30340)")
    parser.add_argument("--end", type=int, help="End ID (default: 36250, +300 weekly after Monday 2026-06-29)")
    args = parser.parse_args()

    # Dynamic ID range calculation:
    # Default start is 30340.
    # Default end is 36250 on the week starting Monday, June 29, 2026.
    # It increases by 300 each subsequent week (Monday).
    ref_date = datetime.date(2026, 6, 29) # Reference Monday
    current_date = datetime.date.today()
    weeks_elapsed = max(0, (current_date - ref_date).days // 7)

    start_id = args.start if args.start is not None else 30340
    end_id = args.end if args.end is not None else (36250 + (weeks_elapsed * 300))

    print(f"Target scraping ID range: {start_id} to {end_id} (weeks elapsed since June 29, 2026: {weeks_elapsed})")
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True, slow_mo=500)
        context = browser.new_context()
        
        try:
            # Login
            login_to_cps_mobile(context)
            
            # Scrape
            df = scrape_po_receive(context, start_id, end_id)
            
            # Save results to MotherDuck
            if not df.empty:
                import duckdb
                import pandas as pd
                print("Connecting to MotherDuck...")
                con = duckdb.connect("md:lake")
                
                # Format data types and align columns with the database schema:
                # ID BIGINT, ReqNumber VARCHAR, PONumber VARCHAR, ReceiveBy VARCHAR, ItemName VARCHAR, Unit VARCHAR, Quantity VARCHAR, ReceiveDate DATE
                df['ID'] = df['ID'].astype(int)
                df['Quantity'] = df['Quantity'].astype(str)
                df['ReceiveDate'] = pd.to_datetime(df['ReceiveDate'], errors='coerce').dt.date
                df = df[['ID', 'ReqNumber', 'PONumber', 'ReceiveBy', 'ItemName', 'Unit', 'Quantity', 'ReceiveDate']]
                
                # Delete existing IDs to avoid duplication (replace on conflict)
                unique_ids = df["ID"].unique().tolist()
                if unique_ids:
                    if len(unique_ids) == 1:
                        con.execute(f"DELETE FROM po_receive_data WHERE ID = {unique_ids[0]}")
                    else:
                        con.execute(f"DELETE FROM po_receive_data WHERE ID IN {tuple(unique_ids)}")
                
                # Insert data
                con.execute("INSERT INTO po_receive_data SELECT * FROM df")
                print("SUCCESS: Data successfully saved to MotherDuck table 'po_receive_data'")
            else:
                print("WARNING: No data was scraped (empty DataFrame).")
                
        except Exception as e:
            print(f"ERROR: An error occurred during scraping execution: {e}")
        finally:
            browser.close()
            print("Browser execution finished.")

if __name__ == "__main__":
    main()
