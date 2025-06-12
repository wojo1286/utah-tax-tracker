Utah Tax Distribution Tracker

This repository automates collecting monthly Utah tax‐distribution data (PDF format) for Transient Room, Tourism Transient Room, Sales & Use, Restaurant, and Resort Communities taxes, filters it for Moab City and Grand County, and loads the results into a Google Sheet. A scheduled GitHub Actions workflow keeps the sheet up‑to‑date.

1 · Project structure

utah-tax-tracker/
├── main.py              # Orchestrates end‑to‑end flow
├── pdf_scraper.py       # Finds & downloads relevant PDFs
├── parser.py            # Extracts tables from each PDF
├── sheets_uploader.py   # Sends cleaned data to Google Sheets
├── requirements.txt     # Python dependencies
└── .github/
    └── workflows/
        └── update-sheet.yml  # CI job that runs main.py on schedule

Tip: keep all scripts at repo root to start. As the project matures you can split into sub‑packages.

2 · Prerequisites

Item

Why

Link

Python 3.10+

local dev & runner image

https://python.org

Google Cloud project

enables Sheets API

https://console.cloud.google.com

Service‑account key (JSON)

headless auth for GitHub Actions

Sheets API → Credentials

GitHub account & new repo

version control & CI

https://github.com

3 · Initial setup

Create the repo

gh repo create utah-tax-tracker --public --clone
cd utah-tax-tracker

Add this README & stub code (copy the snippets below).

Install deps locally

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

Set GitHub Secrets → Repo → Settings → Secrets & variables → Actions

Name

Value

GOOGLE_SERVICE_ACCOUNT_JSON

paste raw JSON

GOOGLE_SHEET_ID

the Sheet’s ID (string between /d/ and /edit)

4 · Code stubs

Below are minimal, working‑toward‑production placeholders. Flesh them out incrementally.

requirements.txt

beautifulsoup4
requests
pdfplumber
pandas
gspread
google-auth

pdf_scraper.py

"""Download monthly tax‑distribution PDFs for the five target tax types."""
from pathlib import Path
import re, requests
from bs4 import BeautifulSoup

BASE = "https://tax.utah.gov/sales/distribution"
PDF_PATTERN = re.compile(r"/(salestax|tourism|resort|restaurant)/distribute/\d{4,}.*\.pdf", re.I)

TAX_KEYWORDS = {
    "Transient Room": "ftr",
    "Tourism Transient Room": "ttr",
    "Sales and Use": "ut",
    "Restaurant": "rest",
    "Resort Communities": "resort",
}

def discover_pdf_links() -> list[str]:
    html = requests.get(BASE, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if PDF_PATTERN.search(href.lower()):
            links.append(requests.compat.urljoin(BASE, href))
    return links

def download_pdfs(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for url in discover_pdf_links():
        fname = url.split("/")[-1]
        path = out_dir / fname
        if not path.exists():
            print(f"Downloading {url}")
            r = requests.get(url, stream=True, timeout=60)
            path.write_bytes(r.content)
        paths.append(path)
    return paths

if __name__ == "__main__":
    download_pdfs(Path("pdfs"))

parser.py

"""Extract tabular amounts for Moab City & Grand County from a PDF."""
import pdfplumber, re, pandas as pd
from pathlib import Path

ENTITY_RE = re.compile(r"\b(Moab|Grand\s+County)\b", re.I)

def parse_pdf(pdf_path: Path) -> pd.DataFrame:
    records = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            for row in table:
                if not row or not row[0]:
                    continue
                text = " ".join((row[0] or "").split())
                if ENTITY_RE.search(text):
                    amount = row[-1].replace(",", "").replace("$", "")
                    try:
                        amount = float(amount)
                    except ValueError:
                        continue
                    records.append({
                        "entity": text,
                        "amount": amount,
                        "pdf": pdf_path.name,
                    })
    return pd.DataFrame(records)

sheets_uploader.py

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

main.py

from pathlib import Path
import pandas as pd
from pdf_scraper import download_pdfs
from parser import parse_pdf
from sheets_uploader import upsert_dataframe

outdir = Path("pdfs")
all_dfs = [parse_pdf(p) for p in download_pdfs(outdir)]
final = pd.concat(all_dfs, ignore_index=True)
upsert_dataframe(final)

.github/workflows/update-sheet.yml

name: Update Google Sheet

on:
  schedule:
    - cron: "0 10 * * 1"   # every Monday 10:00 UTC ≈ 4 am MT
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run extractor
        env:
          GOOGLE_SERVICE_ACCOUNT_JSON: ${{ secrets.GOOGLE_SERVICE_ACCOUNT_JSON }}
          GOOGLE_SHEET_ID: ${{ secrets.GOOGLE_SHEET_ID }}
        run: python main.py

5 · Next steps

Verify parsing quality on a handful of sample PDFs; adjust parser.py regexes or column indices as needed.

Back‑fill history by committing PDFs/CSV extracts or rerunning locally until the Sheet is complete.

Add charts inside Google Sheets (Insert → Chart) or build a Looker Studio dashboard using the same Sheet as data source.

Expand to additional entities or tax types by updating the config or regex filters.

6 · Troubleshooting

Symptom

Likely cause

Fix

Empty DataFrame

Table layout changed

Inspect PDF visually and tweak pdfplumber settings

GitHub Actions fails on auth

Wrong secret value

Ensure entire JSON is pasted and escaped

Duplicate rows

PDFs re‑downloaded & parsed twice

Add deduplication on (entity, pdf) in main.py

7 · License

MIT License (see LICENSE).

