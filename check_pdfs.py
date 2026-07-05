import pdfplumber
import os

pdf_folder = "data/raw_pdfs"

for filename in os.listdir(pdf_folder):
    if filename.endswith(".pdf"):
        path = os.path.join(pdf_folder, filename)
        try:
            with pdfplumber.open(path) as pdf:
                first_page_text = pdf.pages[0].extract_text()
                num_pages = len(pdf.pages)
                if first_page_text and len(first_page_text.strip()) > 50:
                    print(f"✅ {filename}: {num_pages} pages, text extractable")
                else:
                    print(f"⚠️  {filename}: {num_pages} pages, but LOW/NO text (might be scanned)")
        except Exception as e:
            print(f"❌ {filename}: failed to open — {e}")