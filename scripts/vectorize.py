import os
import glob
import json
import argparse
import re
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "memoria")

# Model configuration (Absolutely Free & Local)
# This model is excellent for Portuguese and multilingual contexts
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIMENSION = 384 

# Initialize components lazily or globally for reuse
_model = None
_pc = None

def get_pinecone_index():
    global _pc
    if _pc is None:
        _pc = Pinecone(api_key=PINECONE_API_KEY)
    return _pc.Index(PINECONE_INDEX_NAME)

def get_model():
    global _model
    if _model is None:
        print(f"Loading local model: {MODEL_NAME}...")
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def get_embedding(text: str) -> List[float]:
    """Generate normalized embedding for the given text."""
    model = get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """
    Improved Markdown-aware chunking.
    Splits by headers first, then by paragraphs, then by length.
    """
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for p in paragraphs:
        if len(current_chunk) + len(p) < chunk_size:
            current_chunk += p + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = p + "\n\n"
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

def process_file(file_path: str) -> List[Dict]:
    """Extract content and metadata from a file, adding context to text."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Determine context and metadata
    namespace = "work-context" if "professional" in file_path else "home-context"
    source = os.path.basename(file_path)
    file_type = "documentation" if file_path.endswith('.md') else "code-snippet"
    
    return prepare_chunks(content, source, file_type, namespace, file_path)

def prepare_chunks(content: str, source: str, file_type: str, namespace: str, file_path: str = "") -> List[Dict]:
    """Generic function to chunk and vectorize content."""
    chunks = chunk_text(content)
    processed_chunks = []
    
    for i, chunk in enumerate(chunks):
        enriched_text = f"Source: {source} | Content: {chunk}"
        embedding = get_embedding(enriched_text)
        chunk_id = f"{source}_{i}"
        
        metadata = {
            "source": source,
            "type": file_type,
            "filename": source,
            "filepath": file_path,
            "chunk_index": i,
            "text": chunk[:1000] # Increased snippet size for better context in server
        }
        
        processed_chunks.append({
            "id": chunk_id,
            "values": embedding,
            "metadata": metadata,
            "namespace": namespace
        })
        
    return processed_chunks

def upsert_to_pinecone(data: List[Dict], namespace: str):
    """Upsert vectors to Pinecone after cleaning up old data for the same source."""
    if not data:
        return

    index = get_pinecone_index()
    source = data[0]["metadata"].get("source")
    
    # Pre-emptive cleanup to avoid "zombie" chunks from older versions
    if source:
        try:
            print(f"🧹 Cleaning up existing vectors for: {source}...")
            index.delete(filter={"source": {"$eq": source}}, namespace=namespace)
        except Exception as e:
            # Continue even if delete fails (e.g., if brand new source)
            print(f"⚠️ Cleanup note: {e}")

    to_upsert = [(d["id"], d["values"], d["metadata"]) for d in data]
    index.upsert(vectors=to_upsert, namespace=namespace)

def main():
    parser = argparse.ArgumentParser(description="Vectorize files with optimized retrieval quality.")
    parser.add_argument("--path", type=str, default="docs", help="Path to docs directory")
    args = parser.parse_args()

    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Check index exists or create it
    if PINECONE_INDEX_NAME not in pc.list_indexes().names():
        print(f"Creating index {PINECONE_INDEX_NAME}...")
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )

    # Find all .md and .py files
    files = glob.glob(os.path.join(args.path, "**/*.md"), recursive=True) + \
            glob.glob(os.path.join(args.path, "**/*.py"), recursive=True)

    print(f"Found {len(files)} files to process.")

    for file_path in files:
        print(f"Optimizing index for {file_path}...")
        try:
            processed_data = process_file(file_path)
            if processed_data:
                namespace = processed_data[0]["namespace"]
                upsert_to_pinecone(processed_data, namespace)
                print(f"Successfully optimized {file_path} in {namespace}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    main()
