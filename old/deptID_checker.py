import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoAlertPresentException

# =====================================================
# CONFIG
# =====================================================
USERNAME = "laurentius adi"
PASSWORD = "proc"
START_ID = 5798
END_ID = 6791
OUTPUT_CSV = "id_validation_results.csv"
LOGIN_URL = "https://maa-admin.onlinepo.com"

# =====================================================
# TURBO SCANNER SETUP
# =====================================================
chrome_options = Options()
chrome_options.add_argument("--headless") 
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--blink-settings=imagesEnabled=false") 

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

wait = WebDriverWait(driver, 5)

# Initialize CSV file and write header
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["ProjectID", "Status"])

try:
    # 1. LOGIN ONCE
    print("🌍 Logging in...")
    driver.get(LOGIN_URL)
    
    time.sleep(1.5)
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    if iframes: driver.switch_to.frame(iframes[0])

    wait.until(EC.presence_of_element_located((By.ID, "ASPxPanel2_txtUsername_I"))).send_keys(USERNAME)
    driver.find_element(By.ID, "ASPxPanel2_txtPassword_I").send_keys(PASSWORD)
    driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "ASPxPanel2_btnSignIn_I"))
    
    driver.switch_to.default_content()
    wait.until(lambda d: "Login" not in d.current_url)
    print("🚀 Login successful. Starting Turbo Scan...")

    # 2. VALIDATION LOOP
    for PID in range(START_ID, END_ID + 1):
        driver.switch_to.default_content()
        url = f"https://maa-admin.onlinepo.com/CPS/Forms/Project/BIZ_ProjectDetail.aspx?id={PID}"
        driver.get(url)

        # Buffer for alert detection
        time.sleep(1)
        
        status = "Unknown"
        try:
            alert = driver.switch_to.alert
            status = "Missing"
            alert.accept()
        except NoAlertPresentException:
            # Backup check for data panel
            found = False
            for iframe in driver.find_elements(By.TAG_NAME, "iframe"):
                driver.switch_to.frame(iframe)
                if driver.find_elements(By.ID, "ASPxRoundPanel3"):
                    found = True
                    break
                driver.switch_to.default_content()
            
            status = "VALID" if found else "Dead Link"

        # 3. IMMEDIATE WRITE TO CSV
        print(f"[{'OK' if status == 'VALID' else '!!'}] {PID}: {status}")
        with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([PID, status])

    print(f"\n✅ Scan complete. Results saved to {OUTPUT_CSV}")

finally:
    driver.quit()