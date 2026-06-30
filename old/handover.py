import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ---------- CONFIG ----------
USERNAME = "laurentius adi"
PASSWORD = "proc"

START_ID = 2900
END_ID = 2902

BASE_URL = (
    "https://maa-m.onlinepo.com/"
    "InventoryHandoverDetail.aspx?id={}"
)

LOGIN_URL = "https://maa-m.onlinepo.com"

OUTPUT_CSV = "handover_data.csv"

# ---------- DRIVER SETUP ----------
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

wait = WebDriverWait(driver, 30)
all_rows = []

# ---------- SAFE VALUE ----------
def safe_value(by, locator):
    try:
        return driver.find_element(by, locator).get_attribute("value").strip()
    except:
        return ""

try:
    # ---------- LOGIN ONCE ----------
    driver.get(LOGIN_URL)

    wait.until(EC.presence_of_element_located((By.ID, "tbUserName")))
    driver.find_element(By.ID, "tbUserName").send_keys(USERNAME)
    driver.find_element(By.ID, "tbPassword").send_keys(PASSWORD)
    driver.find_element(By.ID, "btnLogin").click()

    wait.until(lambda d: "Login" not in d.current_url)

    # ---------- ITERATE IDs (SAME PATTERN AS OLD CODE) ----------
    for doc_id in range(START_ID, END_ID + 1):
        print(f"🔄 Processing ID {doc_id}")

        driver.get(BASE_URL.format(doc_id))

        # iframe handling (IDENTICAL to old code)
        driver.switch_to.default_content()
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            driver.switch_to.frame(iframes[0])

        # page marker (LABEL, not value)
        wait.until(EC.presence_of_element_located(
            (By.ID, "MainContent_Label2")
        ))

        # ---------- HEADER ----------
        handover_date = safe_value(By.ID, "MainContent_txtDate")
        receive_by    = safe_value(By.ID, "MainContent_txtCreatedBy")

        # ---------- ITEM TABLE ----------
        rows = driver.find_elements(By.XPATH, "//tbody/tr")
        if not rows:
            continue

        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) != 3:
                continue

            item_name = cols[0].find_element(By.TAG_NAME, "b").text.strip()
            unit = cols[0].text.split("Unit :")[-1].strip()

            info = cols[1].text.split("\n")
            po_number = info[0].replace("PO Number :", "").strip()
            req_number = info[1].replace("Req Number :", "").strip()
            warehouse = info[2].replace("Warehouse :", "").strip()

            quantity = cols[2].text.strip()

            all_rows.append({
                "ID": doc_id,
                "Handover Date": handover_date,
                "Created by": receive_by,
                "ItemName": item_name,
                "Unit": unit,
                "PONumber": po_number,
                "ReqNumber": req_number,
                "Warehouse": warehouse,
                "Quantity": quantity,
            })

    # ---------- WRITE CSV ----------
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "ID",
                "Handover Date",
                "Created by",
                "ItemName",
                "Unit",
                "PONumber",
                "ReqNumber",
                "Warehouse",
                "Quantity",
            ]
        )
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"✅ CSV saved: {OUTPUT_CSV}")

finally:
    driver.quit()
