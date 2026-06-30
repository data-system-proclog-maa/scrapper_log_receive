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

START_ID = 29875
END_ID = 29881

BASE_URL = (
    "https://maa-m.onlinepo.com/"
    "POReceiveAttachment.aspx?mode=view&ID={}"
)

OUTPUT_CSV = "po_receive_data.csv"

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

try:
    # ---------- LOGIN ONCE ----------
    driver.get(BASE_URL.format(START_ID))

    wait.until(EC.presence_of_element_located((By.ID, "tbUserName")))
    driver.find_element(By.ID, "tbUserName").send_keys(USERNAME)
    driver.find_element(By.ID, "tbPassword").send_keys(PASSWORD)
    driver.find_element(By.ID, "btnLogin").click()

    wait.until(lambda d: "Login" not in d.current_url)

    # ---------- ITERATE IDs ----------
    for doc_id in range(START_ID, END_ID + 1):
        print(f"🔄 Processing ID {doc_id}")

        driver.get(BASE_URL.format(doc_id))

        # iframe handling
        driver.switch_to.default_content()
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            driver.switch_to.frame(iframes[0])

        # wait until data exists
        wait.until(lambda d: d.find_element(
            By.ID, "MainContent_txtReqNumber"
        ).get_attribute("value"))

        # ---------- HEADER FIELDS ----------
        req_number = driver.find_element(
            By.ID, "MainContent_txtReqNumber"
        ).get_attribute("value").strip()

        po_number = driver.find_element(
            By.ID, "MainContent_txtPONumber"
        ).get_attribute("value").strip()

        receive_date = driver.find_element(
            By.ID, "MainContent_txtReceiveDate"
        ).get_attribute("value").strip()

        receive_by = driver.find_element(
            By.ID, "MainContent_txtReceiveBy"
        ).get_attribute("value").strip()

        # ---------- ITEM TABLE ----------
        rows = driver.find_elements(By.XPATH, "//tbody/tr")

        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 3:
                all_rows.append({
                    "ID": doc_id,
                    "ReqNumber": req_number,
                    "PONumber": po_number,
                    "ReceiveDate": receive_date,
                    "ReceiveBy": receive_by,
                    "ItemName": cols[0].text.strip(),
                    "Unit": cols[1].text.strip(),
                    "Quantity": cols[2].text.strip(),
                })

    # ---------- WRITE CSV ----------
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "ID",
                "ReqNumber",
                "PONumber",
                "ReceiveDate",
                "ReceiveBy",
                "ItemName",
                "Unit",
                "Quantity"
            ]
        )
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"✅ CSV saved: {OUTPUT_CSV}")

finally:
    driver.quit()
