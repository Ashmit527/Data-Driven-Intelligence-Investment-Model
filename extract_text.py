import pdfplumber

def extract_pdf_text(pdf_path):
    """Extract text from each page of a PDF, keeping pages separate."""
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            pages_text.append({
                "page_number": i + 1,
                "text": text if text else ""
            })
    return pages_text

import os
import json

def process_all_pdfs(pdf_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    for filename in os.listdir(pdf_folder):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_folder, filename)
            print(f"Extracting: {filename}")
            pages = extract_pdf_text(pdf_path)
            
            output_name = filename.replace(".pdf", ".json")
            output_path = os.path.join(output_folder, output_name)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(pages, f, ensure_ascii=False, indent=2)
            print(f"  Saved to {output_path}")

if __name__ == "__main__":
    process_all_pdfs("data/raw_pdfs", "data/extracted_text")