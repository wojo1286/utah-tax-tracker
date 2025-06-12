import os, gspread, pandas as pd
from google.oauth2.service_account import Credentials

SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]

creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
creds = Credentials.from_service_account_info(eval(creds_json), scopes=SCOPE)
client = gspread.authorize(creds)
sheet = client.open_by_key(os.getenv("GOOGLE_SHEET_ID")).worksheet("Raw")

def upsert_dataframe(df: pd.DataFrame):
    if df.empty:
        return
    records = [df.columns.tolist()] + df.values.tolist()
    sheet.clear()
    sheet.update(records, value_input_option="USER_ENTERED")
