import pandas as pd
from bs4 import BeautifulSoup
import os

def scrape_all_local_pages(total_pages=31):
    all_employee_data = []
    files_found = 0

    print(f"--- Starting extraction from {total_pages} files ---")

    for i in range(1, total_pages + 1):
        file_name = f"{i}.html"
        
        if not os.path.exists(file_name):
            print(f"Skipping: {file_name} (File not found)")
            continue
        
        files_found += 1
        with open(file_name, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            
        # Target the table rows
        rows = soup.select("table tbody tr")
        page_count = 0

        for row in rows:
            cells = row.find_all("td")
            
            # Ensure it's a valid data row (Talenta usually has 6+ columns)
            if len(cells) >= 6:
                all_employee_data.append({
                    "Name": cells[0].get_text(strip=True),
                    "ID": cells[1].get_text(strip=True),
                    "Entity": cells[2].get_text(strip=True),
                    "Dept": cells[3].get_text(strip=True),
                    "Position": cells[4].get_text(strip=True),
                    "Email": cells[5].get_text(strip=True),
                    "Source_Page": file_name  # Helpful for debugging which file a row came from
                })
                page_count += 1
        
        print(f"Processed {file_name}: Found {page_count} employees.")

    # --- Finalizing Data ---
    if all_employee_data:
        df = pd.DataFrame(all_employee_data)
        
        # Clean up duplicates (sometimes the same employee appears if pages overlapped during saving)
        initial_count = len(df)
        df.drop_duplicates(subset=["ID", "Email"], keep="first", inplace=True)
        final_count = len(df)

        output_name = "talenta_master_list.csv"
        df.to_csv(output_name, index=False)

        print("\n" + "="*40)
        print(f"SUCCESS!")
        print(f"Files processed: {files_found}")
        print(f"Total rows found: {initial_count}")
        print(f"Unique rows saved: {final_count}")
        print(f"Output file: {output_name}")
        print("="*40)
    else:
        print("\nNo data found. Check if your .html files contain the <table> element.")

if __name__ == "__main__":
    # Ensure this script is in the same folder as your 1.html, 2.html, etc.
    scrape_all_local_pages(31)