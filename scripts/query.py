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

def query_context(query_text: str, namespace: str, top_k: int = 5):
    """Query Pinecone with optimized parameters."""
    print(f"\nSearching in [{namespace}] for: '{query_text}'")
    
    # Generate NORMALIZED embedding for the query
    query_embedding = model.encode(query_text, normalize_embeddings=True).tolist()
    
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

    print(f"\nTop {len(results.matches)} semantic matches found (Cosine Similarity):")
    for i, match in enumerate(results.matches):
        try:
            print(f"\n--- Result {i+1} (Confidence: {match.score:.4f}) ---")
            print(f"Source: {match.metadata.get('source', 'Unknown')}")
            print(f"Type: {match.metadata.get('type', 'Unknown')}")
            
            # Display preview if available, handling potential encoding issues
            if 'text' in match.metadata:
                snippet = match.metadata['text'].replace('\n', ' ')
                # Ensure we can print to terminal by stripping non-encodable chars if needed
                clean_snippet = snippet[:150].encode('ascii', errors='replace').decode('ascii')
                print(f"Preview: {clean_snippet}...")
            
            print(f"Location: {match.metadata.get('filepath', 'Unknown')}")
        except Exception as e:
            print(f"Error displaying result {i+1}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Query the Knowledge Base (Optimized).")
    parser.add_argument("query", type=str, help="The question or topic to search for")
    parser.add_argument("--context", type=str, choices=["pro", "personal"], default="personal", 
                        help="Context to search in (pro -> work-context, personal -> home-context)")
    args = parser.parse_args()

    namespace = "work-context" if args.context == "pro" else "home-context"
    query_context(args.query, namespace)

if __name__ == "__main__":
    main()
