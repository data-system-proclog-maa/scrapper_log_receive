import sys
import os

# Ensure project root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from function.receive_log import login_to_cps, scrape_tr_entry
from playwright.sync_api import sync_playwright

def main():
    print("==========================================")
    print("         TR Entry Scraper Runner          ")
    print("==========================================")
    
    import argparse
    import datetime

    parser = argparse.ArgumentParser(description="TR Entry Scraper Runner")
    parser.add_argument("--start", type=int, help="Start ID (default: 7865)")
    parser.add_argument("--end", type=int, help="End ID (default: 7865, +75 weekly after Monday 2026-01-05)")
    args = parser.parse_args()

    # Dynamic ID range calculation:
    # Default start is 7865.
    # Default end is 7865 on the week starting Monday, Jan 5, 2026.
    # It increases by 75 each subsequent week (Monday).
    ref_date = datetime.date(2026, 1, 5) # Reference Monday
    current_date = datetime.date.today()
    weeks_elapsed = max(0, (current_date - ref_date).days // 7)

    #start_id = args.start if args.start is not None else 7865
    #end_id = args.end if args.end is not None else (7865 + (weeks_elapsed * 75))
    start_id = 1
    end_id = 999
    
    print(f"Target scraping ID range: {start_id} to {end_id} (weeks elapsed since Jan 5, 2026: {weeks_elapsed})")
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True, slow_mo=500)
        context = browser.new_context()
        
        try:
            # Login to CPS Desktop site
            login_to_cps(context)
            
            # Scrape TR entry
            df = scrape_tr_entry(context, start_id, end_id)
            
            # Format and save the results
            if not df.empty:
                import pandas as pd
                df['ID'] = df['ID'].astype(int)
                
                # Split "Item Description" by ";" — keep only the first part as the item name,
                # extract the second part as a new "UoM" column, discard the rest
                if 'Item Description' in df.columns:
                    parts = df['Item Description'].str.split(';', expand=True)
                    df['Item Description'] = parts[0].str.strip()
                    df['UoM'] = parts[1].str.strip() if 1 in parts.columns else ""

                # Reorder columns
                data_cols = ['ID', 'TransferNumber', 'Department', 'PO Number',
                             'Item Description', 'UoM', 'ETA',
                             'Qty Shipped', 'Qty Received', 'Additional Item']
                for col in data_cols:
                    if col not in df.columns:
                        df[col] = ""
                df = df[data_cols]

                # Drop rows where all data columns (everything except ID/TransferNumber) are empty
                cols_to_check = ["Department", "PO Number", "ETA"]

                df = df[
                    ~df[cols_to_check].apply(
                        lambda row: all(pd.isna(v) or str(v).strip() == "" for v in row),
                        axis=1
                    )
                ]
                
                # Save results to a local Parquet file
                output_dir = os.path.join(project_root, 'data')
                os.makedirs(output_dir, exist_ok=True)
                parquet_path = os.path.join(output_dir, 'tr_entry_raw.parquet')
                df.to_parquet(parquet_path, index=False)
                print(f"SUCCESS: {len(df)} rows saved to {parquet_path}")
                print(f"Columns: {list(df.columns)}")
            else:
                print("WARNING: No data was scraped (empty DataFrame).")
                
        except Exception as e:
            print(f"ERROR: An error occurred during scraping execution: {e}")
        finally:
            browser.close()
            print("Browser execution finished.")

if __name__ == "__main__":
    main()