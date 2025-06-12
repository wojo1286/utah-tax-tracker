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
