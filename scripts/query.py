import os
import argparse
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "memoria")
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

# Initialize Local Model
print(f"Loading local model: {MODEL_NAME}...")
model = SentenceTransformer(MODEL_NAME)

def query_context(query_text: str, namespace: str, top_k: int = 3):
    """Query Pinecone for the most relevant context."""
    print(f"\nSearching in [{namespace}] for: '{query_text}'")
    
    # Generate embedding for the query
    query_embedding = model.encode(query_text).tolist()
    
    # Query Pinecone
    results = index.query(
        namespace=namespace,
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    
    if not results.matches:
        print("No matches found.")
        return

    print(f"\nTop {len(results.matches)} matches found:")
    for i, match in enumerate(results.matches):
        print(f"\n--- Result {i+1} (Score: {match.score:.4f}) ---")
        print(f"Source: {match.metadata['source']}")
        print(f"Type: {match.metadata['type']}")
        # We don't store the full text in metadata to save space in this basic version,
        # but in a real RAG you might store snippets or IDs to fetch from a DB.
        # For now, we show the metadata as proof of retrieval.
        print(f"Filename: {match.metadata['filename']}")

def main():
    parser = argparse.ArgumentParser(description="Query the Knowledge Base.")
    parser.add_argument("query", type=str, help="The question or topic to search for")
    parser.add_argument("--context", type=str, choices=["pro", "personal"], default="personal", 
                        help="Context to search in (pro -> work-context, personal -> home-context)")
    args = parser.parse_args()

    namespace = "work-context" if args.context == "pro" else "home-context"
    query_context(args.query, namespace)

if __name__ == "__main__":
    main()
