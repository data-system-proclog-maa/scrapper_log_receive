import sys
import os

# Ensure current directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from receive_log import login_to_cps_mobile, scrape_tl_receive
from playwright.sync_api import sync_playwright

def main():
    print("==========================================")
    print("        TL Receive Scraper Runner         ")
    print("==========================================")
    
    import argparse
    import datetime

    parser = argparse.ArgumentParser(description="TL Receive Scraper Runner")
    parser.add_argument("--start", type=int, help="Start ID (default: 7865)")
    parser.add_argument("--end", type=int, help="End ID (default: 7865, +75 weekly after Monday 2026-06-29)")
    args = parser.parse_args()

    # Dynamic ID range calculation:
    # Default start is 7865.
    # Default end is 7865 on the week starting Monday, June 29, 2026.
    # It increases by 75 each subsequent week (Monday).
    ref_date = datetime.date(2026, 6, 29) # Reference Monday
    current_date = datetime.date.today()
    weeks_elapsed = max(0, (current_date - ref_date).days // 7)

    start_id = args.start if args.start is not None else 7865
    end_id = args.end if args.end is not None else (7865 + (weeks_elapsed * 75))

    print(f"Target scraping ID range: {start_id} to {end_id} (weeks elapsed since June 29, 2026: {weeks_elapsed})")
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True, slow_mo=500)
        context = browser.new_context()
        
        try:
            # Login
            login_to_cps_mobile(context)
            
            # Scrape
            df = scrape_tl_receive(context, start_id, end_id)
            
            # Format data types and align columns with the database schema
            if not df.empty:
                import pandas as pd
                
                df['ID'] = df['ID'].astype(int)
                df['Quantity'] = df['Quantity'].astype(str)
                df['ReceiveDate'] = pd.to_datetime(df['ReceiveDate'], errors='coerce').dt.date
                df = df[['ID', 'TransferNumber', 'ReceiveBy', 'ItemName', 'Unit', 'Quantity', 'ReceiveDate']]
                
                # Save results to a local Parquet file
                output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
                os.makedirs(output_dir, exist_ok=True)
                parquet_path = os.path.join(output_dir, 'tl_receive_raw.parquet')
                df.to_parquet(parquet_path, index=False)
                print(f"SUCCESS: Raw data saved to local Parquet: {parquet_path}")
            else:
                print("WARNING: No data was scraped (empty DataFrame).")
                
        except Exception as e:
            print(f"ERROR: An error occurred during scraping execution: {e}")
        finally:
            browser.close()
            print("Browser execution finished.")

if __name__ == "__main__":
    main()
