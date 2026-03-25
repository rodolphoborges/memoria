import os
import json
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "memoria")

def update_stats():
    if not PINECONE_API_KEY:
        print("❌ PINECONE_API_KEY not found.")
        return

    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    
    try:
        print(f"📡 Fetching stats for index: {PINECONE_INDEX_NAME}")
        stats = index.describe_index_stats()
        
        # Explicitly handle namespace data
        namespaces = stats.get("namespaces", {})
        
        # Safe access to counts
        pro_count = 0
        pers_count = 0
        
        if isinstance(namespaces, dict):
            pro_v = namespaces.get("work-context")
            if isinstance(pro_v, dict):
                pro_count = pro_v.get("vector_count", 0)
            
            pers_v = namespaces.get("home-context")
            if isinstance(pers_v, dict):
                pers_count = pers_v.get("vector_count", 0)

        data = {
            "last_updated": datetime_now_iso(),
            "total_vectors": stats.get("total_vector_count", 0),
            "dimension": stats.get("dimension", 384),
            "contexts": {
                "pro": { "vectors": pro_count },
                "personal": { "vectors": pers_count }
            }
        }
        
        with open("stats.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        print(f"✅ Stats updated. Total: {data['total_vectors']}")

    except Exception as e:
        print(f"❌ Error: {e}")

def datetime_now_iso():
    from datetime import datetime
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

if __name__ == "__main__":
    update_stats()
