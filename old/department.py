import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException

# =====================================================
# CONFIG
# =====================================================
USERNAME = "laurentius adi"
PASSWORD = "proc"

START_ID = 5821
END_ID = 5825

LOGIN_URL = "https://maa-admin.onlinepo.com"
OUTPUT_CSV = "approval_all.csv"

# =====================================================
# DRIVER SETUP
# =====================================================
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

wait = WebDriverWait(driver, 30)
all_rows = []

# =====================================================
# HELPERS (ORIGINAL)
# =====================================================
def safe_text(el):
    try:
        return el.text.strip()
    except:
        return ""

def is_checked(td):
    try:
        span = td.find_element(By.TAG_NAME, "span")
        return "Checked" in span.get_attribute("class")
    except:
        return False

# =====================================================
# TAB SCRAPER (ORIGINAL)
# =====================================================
def scrape_tab(tab_id, table_id_part, approval_type, current_pid, current_dept):
    tab = wait.until(EC.presence_of_element_located((By.ID, tab_id)))
    driver.execute_script("arguments[0].click();", tab)
    time.sleep(1.2)

    wait.until(EC.presence_of_element_located((
        By.XPATH, f"//table[contains(@id,'{table_id_part}')]"
    )))

    rows = driver.find_elements(
        By.XPATH,
        f"//table[contains(@id,'{table_id_part}')]"
        "//tr[contains(@class,'dxgvDataRow')]"
    )

    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) < 4:
            continue

        all_rows.append({
            "ProjectID": current_pid,
            "Department": current_dept,
            "ApprovalType": approval_type,
            "Employee": safe_text(cols[0]),
            "LowerLimit": safe_text(cols[1]),
            "UpperLimit": safe_text(cols[2]),
            "ByPass": "Yes" if is_checked(cols[3]) else "No"
        })

try:
    # LOGIN (ORIGINAL)
    driver.get(LOGIN_URL)
    driver.switch_to.default_content()
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    if iframes:
        driver.switch_to.frame(iframes[0])

    wait.until(EC.presence_of_element_located((By.ID, "ASPxPanel2_txtUsername_I")))
    driver.find_element(By.ID, "ASPxPanel2_txtUsername_I").send_keys(USERNAME)
    driver.find_element(By.ID, "ASPxPanel2_txtPassword_I").send_keys(PASSWORD)
    login_btn = driver.find_element(By.ID, "ASPxPanel2_btnSignIn_I")
    driver.execute_script("arguments[0].click();", login_btn)

    driver.switch_to.default_content()
    wait.until(lambda d: "Login" not in d.current_url)

    # =================================================
    # LOOP THROUGH RANGE
    # =================================================
    for PROJECT_ID in range(START_ID, END_ID + 1):
        try:
            # FORCE RESET TO MAIN PAGE FOR EVERY ID
            driver.switch_to.default_content()
            
            print(f"Processing ID: {PROJECT_ID}")
            PROJECT_URL = f"https://maa-admin.onlinepo.com/CPS/Forms/Project/BIZ_ProjectDetail.aspx?id={PROJECT_ID}"
            
            driver.get(PROJECT_URL)
            
            # Wait a moment for the page/alert to trigger
            time.sleep(1.5)

            # 1. HANDLE ALERT IF PRESENT
            try:
                alert = driver.switch_to.alert
                print(f"⚠️ Skipping ID {PROJECT_ID}: {alert.text}")
                alert.accept()
                continue 
            except NoAlertPresentException:
                pass

            # 2. FIND IFRAME (ORIGINAL LOCATORS)
            found_iframe = False
            # Wait until at least one iframe is present before searching
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
            
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                driver.switch_to.frame(iframe)
                try:
                    # Original Locator check
                    driver.find_element(By.ID, "ASPxRoundPanel3")
                    found_iframe = True
                    break
                except:
                    driver.switch_to.default_content()

            if not found_iframe:
                print(f"❌ ID {PROJECT_ID}: Required panel not found (Skipping).")
                continue

            # 3. SCRAPE (ORIGINAL LOCATORS)
            department_name = wait.until(EC.presence_of_element_located((
                By.ID, "ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolder1_ASPxRoundPanel3_ASPxRoundPanel6_txtProjectName_I"
            ))).get_attribute("value")

            scrape_tab("ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolder1_ASPxRoundPanel3_pageTab_T0T", "dgRequisitonApprovalList", "Requisition Approval", PROJECT_ID, department_name)
            scrape_tab("ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolder1_ASPxRoundPanel3_pageTab_T1T", "dgRequisitonConsignmentApprovalList", "Requisition Consignment Approval", PROJECT_ID, department_name)
            scrape_tab("ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolder1_ASPxRoundPanel3_pageTab_T2T", "dgRequisitonContractApprovalList", "Requisition Fix Price Approval", PROJECT_ID, department_name)
            scrape_tab("ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolder1_ASPxRoundPanel3_pageTab_T3T", "dgPOApprovalList", "Purchase Order Approval", PROJECT_ID, department_name)
            scrape_tab("ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolder1_ASPxRoundPanel3_pageTab_T4T", "dgPOConsignmentApprovalList", "Purchase Order - Consignment Approval", PROJECT_ID, department_name)
            scrape_tab("ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolder1_ASPxRoundPanel3_pageTab_T5T", "dgPOContractApprovalList", "Purchase Order - Fix Price Approval", PROJECT_ID, department_name)

        except UnexpectedAlertPresentException:
            try:
                driver.switch_to.alert.accept()
            except:
                pass
            continue
        except Exception as e:
            print(f"❌ Skipping ID {PROJECT_ID} due to error: {e}")
            continue

    # WRITE CSV (ORIGINAL)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ProjectID", "Department", "ApprovalType", "Employee", "LowerLimit", "UpperLimit", "ByPass"])
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"✅ CSV saved: {OUTPUT_CSV}")

finally:
    driver.quit()