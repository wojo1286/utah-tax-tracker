from pathlib import Path
import pandas as pd
from pdf_scraper import download_pdfs
from parser import parse_pdf
from sheets_uploader import upsert_dataframe

outdir = Path("pdfs")
all_dfs = [parse_pdf(p) for p in download_pdfs(outdir)]
final = pd.concat(all_dfs, ignore_index=True)
upsert_dataframe(final)
