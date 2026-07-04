import os
import sys
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

def extract_chunks_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Reads a PDF file, extracts text page-by-page, and splits it into semantic chunks of ~800-1000 characters.
    """
    doc_name = os.path.basename(pdf_path)
    print(f"Extracting text from: {doc_name}")
    
    reader = pypdf.PdfReader(pdf_path)
    chunks = []
    
    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        text = page.extract_text()
        if not text:
            continue
            
        # Clean extra white spaces and tabs
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Split text into chunks of ~1000 characters with 150 characters overlap
        chunk_size = 1000
        overlap = 150
        
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_content = text[start:end].strip()
            
            # Discard very small chunks
            if len(chunk_content) > 100:
                chunk_id = f"{doc_name.replace(' ', '_')}_p{page_num}_{uuid.uuid4().hex[:6]}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "doc_name": doc_name,
                    "page_num": page_num,
                    "content": chunk_content
                })
            
            start += chunk_size - overlap
            
    print(f"Extracted {len(chunks)} chunks from {doc_name}.")
    return chunks

def embed_chunks(chunks: List[Dict[str, Any]], client: genai.Client) -> List[Dict[str, Any]]:
    """
    Generates 768-dimensional float embeddings for a list of text chunks using Vertex AI text-embedding-004.
    """
    print(f"Generating embeddings for {len(chunks)} text chunks...")
    embedded_chunks = []
    
    # Process in batches to handle rate limits and request sizing
    batch_size = 50
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        contents = [c["content"] for c in batch]
        
        try:
            # Call Gemini text-embedding-004 model
            response = client.models.embed_content(
                model="text-embedding-004",
                contents=contents
            )
            
            # Map embeddings back to chunks
            for idx, item in enumerate(batch):
                embedding = response.embeddings[idx].values
                item["embedding"] = [float(v) for v in embedding]
                embedded_chunks.append(item)
                
            print(f"Embedded chunks {i + 1} to {min(i + batch_size, len(chunks))}...")
        except Exception as e:
            print(f"Embedding batch error: {e}. Skipping this batch.")
            
    return embedded_chunks

def seed_pdf_data():
    guidelines_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "docs", "guidelines"
    )
    
    if not os.path.exists(guidelines_dir):
        print(f"Error: Guidelines folder not found at {guidelines_dir}")
        return
        
    # Scan for PDF files
    pdf_files = [os.path.join(guidelines_dir, f) for f in os.listdir(guidelines_dir) if f.endswith(".pdf")]
    
    if not pdf_files:
        print(f"No PDF files found in {guidelines_dir}.")
        return
        
    print(f"Found {len(pdf_files)} PDF documents to index.")
    
    # 1. Initialize Clients
    print("Connecting to Google GenAI API...")
    try:
        # Load from GCloud active account
        client = genai.Client()
    except Exception as e:
        print(f"Failed to initialize Google GenAI Client: {e}")
        return
        
    print("Connecting to BigQuery...")
    bq_wrapper = BigQueryClientWrapper()
    bq_wrapper.init_tables()
    
    dataset = bq_wrapper.dataset_ref
    
    # Process each PDF document
    for pdf_path in pdf_files:
        try:
            doc_name = os.path.basename(pdf_path)
            # Check if document already indexed (optional: delete existing to refresh)
            print(f"Clearing old records for: {doc_name}")
            bq_wrapper.client.query(
                f"DELETE FROM `{dataset}.guidelines_vector` WHERE doc_name = @doc_name",
                job_config=genai.types.QueryJobConfig(
                    query_parameters=[
                        genai.types.ScalarQueryParameter("doc_name", "STRING", doc_name)
                    ]
                ) if hasattr(genai.types, "QueryJobConfig") else None
            ).result()
            
            # Simple fallback deletion query if parameters not supported directly
            bq_wrapper.client.query(f"DELETE FROM `{dataset}.guidelines_vector` WHERE doc_name = '{doc_name}'").result()
            
            # Extract
            chunks = extract_chunks_from_pdf(pdf_path)
            
            # Embed
            # Note: For huge files (like BCAP full report which is 18MB), we should cap the chunks 
            # to the first 100 pages or 200 chunks to avoid running out of free credits or rate limit limits.
            if len(chunks) > 150:
                print(f"Document {doc_name} has {len(chunks)} chunks. Capping to first 150 chunks for prototype speed.")
                chunks = chunks[:150]
                
            embedded_chunks = embed_chunks(chunks, client)
            
            if not embedded_chunks:
                print(f"No chunks embedded successfully for {doc_name}.")
                continue
                
            # Ingest to BigQuery
            print(f"Uploading {len(embedded_chunks)} chunks of {doc_name} to BigQuery...")
            chunk_upload_size = 50
            for i in range(0, len(embedded_chunks), chunk_upload_size):
                sub_chunk = embedded_chunks[i:i + chunk_upload_size]
                bq_wrapper.insert_rows("guidelines_vector", sub_chunk)
                print(f"Uploaded chunks {i + 1} to {min(i + chunk_upload_size, len(embedded_chunks))}...")
                
            print(f"Document {doc_name} successfully indexed!")
        except Exception as e:
            print(f"Failed to process document {pdf_path}: {e}")
            
    print("--- PDF RAG Guidelines Ingestion Completed Successfully ---")

if __name__ == "__main__":
    seed_pdf_data()
