"""Build a searchable page corpus from the bundled IPC book."""
import csv
from pathlib import Path
import pymupdf

base = Path(__file__).resolve().parent
source = base.parent / "LegalLaw" / "Chatbot" / "Indian Penal Code Book.pdf"
target = base / "instance" / "ipc_corpus.csv"
target.parent.mkdir(parents=True, exist_ok=True)
count = 0
with pymupdf.open(source) as book, target.open("w", newline="", encoding="utf-8") as output:
    writer = csv.DictWriter(output, fieldnames=["text", "name"])
    writer.writeheader()
    for page_number, page in enumerate(book, start=1):
        text = page.get_text().strip()
        if len(text.split()) < 10:
            continue
        writer.writerow({"text": text, "name": f"IPC Book - page {page_number}"})
        count += 1
print(f"Prepared {count} searchable pages: {target}")
print("Set DATA_PATH=backend/instance/ipc_corpus.csv in backend/.env and restart the backend.")
