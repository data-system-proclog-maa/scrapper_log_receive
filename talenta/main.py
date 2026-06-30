from playwright.sync_api import sync_playwright
import pandas as pd
import time

def scrape_talenta_fixed():
    with sync_playwright() as p:
        # Launch visible browser
        browser = p.chromium.launch(headless=False, slow_mo=600) 
        context = browser.new_context()
        page = context.new_page()

        # 1. Login
        print("Logging in...")
        page.goto("https://hr.talenta.co")
        page.fill("#user_email", "kristianto.adiwicaksono@gmail.com")
        page.fill("#user_password", "Adi&19125514")
        page.click("#new-signin-button")
        page.wait_for_load_state("networkidle")

        # 2. Navigate to Address Book
        print("Opening Employee Address Book...")
        page.click('a[href="/employee/address-book?id=A"]')
        page.wait_for_load_state("networkidle")
        
        # 3. Set rows per page to 100 (Improved logic)
        print("Setting rows to 100...")
        dropdown_selector = "select.custom-select"
        page.wait_for_selector(dropdown_selector)
        
        # Select 100 and then dispatch a 'change' event to make sure Vue knows we changed it
        page.select_option(dropdown_selector, value="100")
        page.eval_on_selector(dropdown_selector, "el => el.dispatchEvent(new Event('change', { bubbles: true }))")
        
        print("Waiting for table to reload 100 rows...")
        time.sleep(5) # Give it extra time to refresh

        all_employee_data = []
        current_page = 1
        max_pages = 31

        while current_page <= max_pages:
            print(f"Scraping Page {current_page} of {max_pages}...")
            
            # IMPROVED: Wait for the first row of the table to be visible 
            # and ensure it's not the "No Data" row.
            try:
                page.wait_for_selector("table tbody tr td", timeout=10000)
            except:
                print("Timeout waiting for table data. Retrying once...")
                time.sleep(5)

            rows = page.query_selector_all("table tbody tr")
            
            page_rows_count = 0
            current_page_data = []
            for row in rows:
                cells = row.query_selector_all("td")
                if len(cells) >= 6:
                    current_page_data.append({
                        "Name": cells[0].inner_text().strip(),
                        "ID": cells[1].inner_text().strip(),
                        "Entity": cells[2].inner_text().strip(),
                        "Dept": cells[3].inner_text().strip(),
                        "Position": cells[4].inner_text().strip(),
                        "Email": cells[5].inner_text().strip()
                    })
                    page_rows_count += 1
            
            # If we got 0 rows, the page might still be loading. 
            # Let's try one more short sleep and a re-scrape.
            if page_rows_count == 0:
                print("Page appeared empty, waiting 5 more seconds...")
                time.sleep(5)
                continue # Re-run this loop iteration for the same page

            all_employee_data.extend(current_page_data)
            print(f"Captured {page_rows_count} employees from this page.")

            if current_page == max_pages:
                break

            # 5. Handle Pagination
            next_button = page.locator('button[title="Next"]')
            is_disabled = next_button.evaluate("node => node.disabled || node.classList.contains('disabled')")
            
            if next_button.is_visible() and not is_disabled:
                print("Clicking Next...")
                # Force a small wait so we don't click faster than the UI can handle
                next_button.click()
                current_page += 1
                # Wait for the old data to disappear so we don't scrape Page 6 twice
                time.sleep(2) 
            else:
                print("Next button is disabled or not found. Stopping.")
                break

            # 5. Handle Pagination (Fixed Logic)
            # We check if the button is "disabled" via class/attribute rather than is_enabled()
            next_button = page.locator('button[title="Next"]')
            
            # Check if button exists and is not visually disabled
            is_disabled = next_button.evaluate("node => node.disabled || node.classList.contains('disabled')")
            
            if next_button.is_visible() and not is_disabled:
                print("Clicking Next...")
                next_button.click()
                current_page += 1
                time.sleep(4) # Wait for next page to load
            else:
                print("Next button is disabled or not found. Stopping.")
                break

        # 6. Save Data
        if all_employee_data:
            df = pd.DataFrame(all_employee_data)
            df.to_csv("talenta_employees_final.csv", index=False)
            print(f"\n--- DONE! Saved {len(all_employee_data)} rows to 'talenta_employees_final.csv' ---")
        else:
            print("No data was scraped. Check if the table loaded correctly.")

        page.pause()
        browser.close()

if __name__ == "__main__":
    scrape_talenta_fixed()