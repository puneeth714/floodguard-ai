import os
import sys
import argparse
import re
import uuid
import pypdf
from typing import List, Dict, Any
from google import genai
from dotenv import load_dotenv

# Add backend to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.bigquery_client import BigQueryClientWrapper

# Load env variables (for GCloud credentials)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

VALID_CATEGORIES = {"ENGINEERING", "MITIGATION", "CLIMATE", "ADMIN", "EMERGENCY", "CLAIMS"}

def extract_chunks(pdf_path: str, category: str) -> List[Dict[str, Any]]:
    """
    Reads a PDF and yields semantic chunks tagged with the category and parsed section headers.
    """
    doc_name = os.path.basename(pdf_path)
    reader = pypdf.PdfReader(pdf_path)
    chunks = []
    
    current_section = "General Introduction"
    
    print(f"Parsing pages from {doc_name}...")
    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        text = page.extract_text()
        if not text:
            continue
            
        # Basic Section Header detection (e.g. lines starting with numbers or all caps)
        lines = text.split('\n')
        for line in lines[:5]:  # Look near the top of the page for headers
            cleaned_line = line.strip()
            # Match patterns like: "1. Introduction", "SECTION III", "EXECUTIVE SUMMARY"
            if re.match(r'^(?:[0-9]+(?:\.[0-9]+)*|[IVXLCDM]+\.?)\s+[A-Z]', cleaned_line) or (cleaned_line.isupper() and len(cleaned_line) > 5 and len(cleaned_line) < 60):
                current_section = cleaned_line
                break
                
        # Clean whitespaces
        cleaned_text = re.sub(r'\s+', ' ', text).strip()
        
        # Chunk text (approx 1000 chars, with 150 chars overlap)
        chunk_size = 1000
        overlap = 150
        
        start = 0
        while start < len(cleaned_text):
            end = min(start + chunk_size, len(cleaned_text))
            chunk_content = cleaned_text[start:end].strip()
            
            if len(chunk_content) > 100:
                chunk_id = f"{category.lower()}_{uuid.uuid4().hex[:8]}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "doc_name": doc_name,
                    "page_num": page_num,
                    "section_title": current_section,
                    "category": category,
                    "content": chunk_content
                })
            start += chunk_size - overlap
            
    return chunks

def embed_and_upload(chunks: List[Dict[str, Any]], bq_wrapper: BigQueryClientWrapper, client: genai.Client):
    """
    Calls Gemini API to generate embeddings and streams the rows into BigQuery.
    """
    print(f"Generating embeddings for {len(chunks)} chunks...")
    batch_size = 30
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        contents = [c["content"] for c in batch]
        
        # Get embeddings
        response = client.models.embed_content(
            model="text-embedding-004",
            contents=contents
        )
        
        # Map embeddings to rows
        rows = []
        for idx, item in enumerate(batch):
            embedding_vals = response.embeddings[idx].values
            rows.append({
                "chunk_id": item["chunk_id"],
                "doc_name": item["doc_name"],
                "page_num": item["page_num"],
                "section_title": item["section_title"],
                "category": item["category"],
                "content": item["content"],
                "embedding": [float(v) for v in embedding_vals]
            })
            
        # Upload
        bq_wrapper.insert_rows("guidelines_vector", rows)
        print(f"Successfully uploaded chunks {i + 1} to {min(i + batch_size, len(chunks))}...")

def main():
    parser = argparse.ArgumentParser(description="Modular PDF Document Indexer for BigQuery Vector Search")
    parser.add_argument("--file", required=True, help="Path to the PDF file to index")
    parser.add_argument("--category", required=True, help=f"Category tag. Must be one of: {', '.join(VALID_CATEGORIES)}")
    
    args = parser.parse_args()
    
    category = args.category.upper()
    if category not in VALID_CATEGORIES:
        print(f"Error: Invalid category '{args.category}'. Must be one of: {VALID_CATEGORIES}")
        sys.exit(1)
        
    pdf_path = args.file
    if not os.path.exists(pdf_path):
        # Check relative path to root too
        root_relative = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), pdf_path)
        if os.path.exists(root_relative):
            pdf_path = root_relative
        else:
            print(f"Error: File not found at '{args.file}'")
            sys.exit(1)
            
    doc_name = os.path.basename(pdf_path)
    print(f"\n==========================================")
    print(f"Starting modular indexing for: {doc_name}")
    print(f"Category: {category}")
    print(f"==========================================")
    
    # 1. Initialize Clients
    print("Connecting to Google APIs...")
    try:
        client = genai.Client(vertexai=True, project="floodguardai-501409", location="us-central1")
        bq_wrapper = BigQueryClientWrapper()
        bq_wrapper.init_tables() # Re-creates guidelines_vector if dropped
    except Exception as e:
        print(f"Error initializing client wrappers: {e}")
        sys.exit(1)
        
    # Clear old entries for this specific document to prevent duplicates
    dataset = bq_wrapper.dataset_ref
    print(f"Clearing old guidelines entries for: {doc_name}")
    bq_wrapper.client.query(f"DELETE FROM `{dataset}.guidelines_vector` WHERE doc_name = '{doc_name}'").result()
    
    # 2. Extract Chunks
    chunks = extract_chunks(pdf_path, category)
    
    if not chunks:
        print("No valid text chunks found in PDF. Indexing cancelled.")
        sys.exit(1)
        
    # 3. Cap chunks for prototype safety (prevents rate limit issues on large PDFs)
    # The BCAP report and media PDF are massive (18-20MB). We cap to 120 chunks to index the key parts.
    MAX_CHUNKS = 120
    if len(chunks) > MAX_CHUNKS:
        print(f"Warning: Document has {len(chunks)} chunks. Capping to first {MAX_CHUNKS} chunks for prototype speed and quota safety.")
        chunks = chunks[:MAX_CHUNKS]
        
    # 4. Embed & Upload
    try:
        embed_and_upload(chunks, bq_wrapper, client)
        print(f"\nSuccessfully indexed {len(chunks)} chunks for '{doc_name}' under category '{category}'!")
    except Exception as e:
        print(f"Indexing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
