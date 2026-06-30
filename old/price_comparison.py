import os
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ============================================================
# PATH SETUP
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ============================================================
# CONFIG
# ============================================================
USERNAME = "laurentius adi"
PASSWORD = "proc"

START_ID = 32256
END_ID = 32257

BASE_URL = (
    "https://maa-admin.onlinepo.com/"
    "CPS/Forms/Project/BIZ_PODetail.aspx?POID={}"
)
LOGIN_URL = "https://maa-admin.onlinepo.com"

# ============================================================
# DRIVER SETUP
# ============================================================
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--log-level=3")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)
wait = WebDriverWait(driver, 60)

try:
    # ========================================================
    # LOGIN
    # ========================================================
    driver.get(LOGIN_URL)

    wait.until(EC.presence_of_element_located(
        (By.ID, "ASPxPanel2_txtUsername_I")
    ))
    driver.find_element(By.ID, "ASPxPanel2_txtUsername_I").send_keys(USERNAME)
    driver.find_element(By.ID, "ASPxPanel2_txtPassword_I").send_keys(PASSWORD)

    driver.execute_script(
        "document.getElementById('ASPxPanel2_btnSignIn').click();"
    )
    wait.until(lambda d: "Login" not in d.current_url)
    print("✅ Login successful")

    # ========================================================
    # REQUEST SESSION (FOR FILE DOWNLOAD)
    # ========================================================
    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie["name"], cookie["value"])

    # ========================================================
    # LOOP POID
    # ========================================================
    for po_id in range(START_ID, END_ID + 1):
        print(f"\n🔎 Processing POID {po_id}")
        driver.get(BASE_URL.format(po_id))

        try:
            wait.until(EC.presence_of_element_located(
                (By.ID, "ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolder1_ASPxRoundPanel3")
            ))

            # ====================================================
            # EXTRACT PO NUMBER
            # ====================================================
            po_number = driver.execute_script("""
                function findPONumber(win) {
                    try {
                        let i = win.document.querySelector("input[id$='txtPONumber_I']");
                        if (i && i.value) return i.value;
                        for (let f of win.frames) {
                            let v = findPONumber(f);
                            if (v) return v;
                        }
                    } catch(e){}
                    return null;
                }
                return findPONumber(window);
            """) or f"POID_{po_id}"

            safe_po = po_number.replace("/", "_")

            # ====================================================
            # CLICK PO COMMENT & ATTACHMENT TAB
            # ====================================================
            tab = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//span[contains(text(),'PO Comment')]")
            ))
            driver.execute_script("arguments[0].click();", tab)
            time.sleep(2)

            # ====================================================
            # FIND ATTACHMENTS (VISIBLE + UNIQUE)
            # ====================================================
            anchors = driver.find_elements(
                By.XPATH, "//a[contains(@href,'DownloadAttachment.aspx')]"
            )

            seen = set()
            for a in anchors:
                if not a.is_displayed():
                    continue

                url = a.get_attribute("href")
                if url in seen:
                    continue
                seen.add(url)

                original_name = a.text.strip() or "attachment.pdf"

                # =================================================
                # FIND DATE (SAME MESSAGE BLOCK)
                # =================================================
                date_text = ""
                spans = a.find_elements(
                    By.XPATH,
                    ".//ancestor::div[1]//span[contains(@id,'lblDate') and normalize-space()]"
                )

                if spans:
                    date_text = spans[0].text.strip()

                # =================================================
                # IGNORE AM/PM & PARSE DATE
                # =================================================
                formatted_date = "unknown_date"
                if date_text:
                    clean_date = (
                        date_text
                        .replace("AM", "")
                        .replace("PM", "")
                        .strip()
                    )
                    try:
                        dt = datetime.strptime(clean_date, "%B %d %Y at %H:%M")
                        formatted_date = dt.strftime("%Y-%m-%d_%H-%M")
                    except Exception:
                        print(f"⚠ Date parse failed: {clean_date}")

                # =================================================
                # SAFE FILE NAME
                # =================================================
                safe_name = (
                    original_name
                    .replace("/", "_")
                    .replace("\\", "_")
                    .replace(":", "_")
                    .replace("*", "_")
                    .replace("?", "")
                    .replace('"', "")
                    .replace("<", "")
                    .replace(">", "")
                    .replace("|", "")
                )

                final_name = f"{safe_po} - {formatted_date} - {safe_name}"
                filepath = os.path.join(DOWNLOAD_DIR, final_name)

                print(f"⬇ Downloading: {final_name}")

                r = session.get(url, timeout=30)
                r.raise_for_status()

                with open(filepath, "wb") as f:
                    f.write(r.content)

                print("✅ Saved")

        except Exception as e:
            print(f"❌ Error POID {po_id}: {e}")

finally:
    driver.quit()
    print("\n🚀 Done")
