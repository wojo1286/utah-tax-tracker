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
