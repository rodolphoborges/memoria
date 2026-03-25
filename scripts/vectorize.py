import os
import glob
import json
import argparse
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
EMBEDDING_DIMENSION = 384 # Dimension for this specific model

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# Initialize Local Model
print(f"Loading local model: {MODEL_NAME}...")
model = SentenceTransformer(MODEL_NAME)

def get_embedding(text: str) -> List[float]:
    """Generate embedding for the given text using local sentence-transformers."""
    embedding = model.encode(text)
    return embedding.tolist()

def chunk_text(text: str, chunk_size: int = 1000) -> List[str]:
    """Simple text chunking."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def process_file(file_path: str) -> List[Dict]:
    """Extract content and metadata from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Determine context and metadata
    namespace = "work-context" if "professional" in file_path else "home-context"
    source = os.path.basename(file_path)
    file_type = "documentation" if file_path.endswith('.md') else "code-snippet"
    
    chunks = chunk_text(content)
    processed_chunks = []
    
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        chunk_id = f"{source}_{i}"
        
        metadata = {
            "source": source,
            "type": file_type,
            "filename": os.path.basename(file_path),
            "filepath": file_path,
            "chunk_index": i
        }
        
        processed_chunks.append({
            "id": chunk_id,
            "values": embedding,
            "metadata": metadata,
            "namespace": namespace
        })
        
    return processed_chunks

def upsert_to_pinecone(data: List[Dict], namespace: str):
    """Upsert vectors to Pinecone."""
    index = pc.Index(PINECONE_INDEX_NAME)
    to_upsert = [(d["id"], d["values"], d["metadata"]) for d in data]
    index.upsert(vectors=to_upsert, namespace=namespace)

def main():
    parser = argparse.ArgumentParser(description="Vectorize files using free local embeddings.")
    parser.add_argument("--path", type=str, default="docs", help="Path to docs directory")
    args = parser.parse_args()

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
        print(f"Processing {file_path}...")
        try:
            processed_data = process_file(file_path)
            if processed_data:
                namespace = processed_data[0]["namespace"]
                upsert_to_pinecone(processed_data, namespace)
                print(f"Successfully upserted {file_path} to {namespace}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    main()
