import os
import duckdb
import gspread
import pandas as pd
from dotenv import load_dotenv

# Load environment variables (MOTHERDUCK_TOKEN)
load_dotenv()

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
json_path = os.path.join(project_root, 'warehouse-482513-222256d39fd6.json')

# 1. Authenticate with Google Sheets (requires service_account.json)
gc = gspread.service_account(filename=json_path)

# 2. Open spreadsheet and select worksheet
sh = gc.open_by_key('1EZ7kPPvnRqvR5UN0Vi0NNLpLTNXEArzRklsVTIGb1vc')
sh2 = gc.open_by_key('1x0VStaJ4EVrZt3A2HlWhlBH8ffjq3giV5SLImz_8S8A')
normalisasi_rfm = sh.worksheet('normalisasi_rfm')
normalisasi_rfm_solar = sh.worksheet('normalisasi_rfm_solar')
normalisasi_po = sh.worksheet('normalisasi_po')
notcalculated_po = sh.worksheet('notcalculated_po')
normalisasi_logistic = sh.worksheet('normalisasi_logistic')
non_workdays = sh.worksheet('non_workdays')
periodic_non_workdays = sh.worksheet('periodic_non_workdays')
shipment_seafreight = sh2.worksheet('Seafreight')
shipment_airfreight = sh2.worksheet('airfreight_baru')

# 3. Read data into pandas DataFrame
df1 = pd.DataFrame(normalisasi_rfm.get_all_records())
df2 = pd.DataFrame(normalisasi_rfm_solar.get_all_records())
data = normalisasi_po.get('A:B')
df3 = pd.DataFrame(data[1:], columns=data[0])
df4 = pd.DataFrame(notcalculated_po.get_all_records())
df5 = pd.DataFrame(normalisasi_logistic.get_all_records())
df6 = pd.DataFrame(non_workdays.get_all_records())
df7 = pd.DataFrame(periodic_non_workdays.get_all_records())
df8 = pd.DataFrame(shipment_seafreight.get_all_records())
df9 = pd.DataFrame(shipment_airfreight.get_all_records())

# 4. Save DataFrame into MotherDuck table
#token = os.getenv("MOTHERDUCK_TOKEN")
#con = duckdb.connect(f"md:lake?token={token}") if token else duckdb.connect("md:lake")
con = duckdb.connect("md:lake")
con.execute("CREATE TABLE IF NOT EXISTS processing_proclog.normalisasi_rfm AS SELECT * FROM df1;")
con.execute("CREATE TABLE IF NOT EXISTS processing_proclog.normalisasi_rfm_solar AS SELECT * FROM df2;")
con.execute("CREATE TABLE IF NOT EXISTS processing_proclog.normalisasi_po AS SELECT * FROM df3;")
con.execute("CREATE TABLE IF NOT EXISTS processing_proclog.notcalculated_po AS SELECT * FROM df4;")
con.execute("CREATE TABLE IF NOT EXISTS processing_proclog.normalisasi_logistic AS SELECT * FROM df5;")
con.execute("CREATE TABLE IF NOT EXISTS processing_proclog.non_workdays AS SELECT * FROM df6;")
con.execute("CREATE TABLE IF NOT EXISTS processing_proclog.periodic_non_workdays AS SELECT * FROM df7;")
con.execute("CREATE TABLE IF NOT EXISTS shipment.seafreight AS SELECT * FROM df8;")
con.execute("CREATE TABLE IF NOT EXISTS shipment.airfreight AS SELECT * FROM df9;")
print("Private Google Sheet data loaded into MotherDuck!")
