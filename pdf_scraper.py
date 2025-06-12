"""Download monthly tax‑distribution PDFs only for our four target tax types
without scraping every link on the web page.  We construct the filenames
because the Utah Tax Commission follows a predictable pattern:

    {YY}{MM}{prefix}{TAX_ID}.pdf

* **{YY}{MM}** – last two digits of the year + zero‑padded month.  Example:
  `2505` → May 2025.
* **prefix** – All tax files insert `ut_` between the `{YY}{MM}` stamp and the tax code (e.g., `2505ut_ftr035.pdf`).
* **TAX_ID**   – unique code for each tax type:

    - Sales & Use         → `ftr022`
    - Transient Room      → `ftr023`
    - Restaurant          → `ftr031`
    - Resort Communities  → `ftr035` (Moab‑only, Grand County not present)

Any URL that returns **HTTP 200** with a PDF is downloaded; 404s are skipped.
This saves bandwidth and avoids downloading irrelevant PDFs.
"""
from pathlib import Path
import datetime, requests

BASE = "https://tax.utah.gov/salestax/distribute"
TAX_IDS = {
    "Sales and Use": "ftr022",
    "Transient Room": "ftr023",
    "Restaurant": "ftr031",
    "Resort Communities": "ftr035",
}

# Adjust if you discover earlier archives
START_YEAR = 1998  # earliest year you want to probe


def month_year_iter(start_y: int, end: datetime.date):
    """Yield (year, month) tuples from Jan start_y through end (inclusive)."""
    for year in range(start_y, end.year + 1):
        for month in range(1, 13):
            current = datetime.date(year, month, 1)
            if current > end.replace(day=1):
                return
            yield year, month


def build_urls():
    """Generate candidate URLs plus metadata."""
    today = datetime.date.today()
    for year, month in month_year_iter(START_YEAR, today):
        ym = f"{str(year)[-2:]}{month:02d}"
        for tax, code in TAX_IDS.items():
            prefix = "ut_"
            url = f"{BASE}/{ym}{prefix}{code}.pdf"
            yield url, tax, year, month


def download_pdfs(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for url, tax, y, m in build_urls():
        fname = url.split("/")[-1]
        path = out_dir / fname
        if path.exists():
            paths.append(path)
            continue
        resp = requests.get(url, stream=True, timeout=20)
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("application/pdf"):
            path.write_bytes(resp.content)
            paths.append(path)
            print(f"✓ {tax} {y}-{m:02d} downloaded → {fname}")
    return paths


if __name__ == "__main__":
    download_pdfs(Path("pdfs"))
