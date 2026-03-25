"""
memoria_server.py — Context Provider HTTP para o Continue.dev

Expõe o Pinecone do projeto Memória como fonte de contexto no VSCodium.

INSTALAÇÃO:
    pip install fastapi uvicorn sentence-transformers pinecone python-dotenv

USO:
    python memoria_server.py

    Deixe rodando em background enquanto usa o VSCodium.
    O Continue vai consultar http://localhost:8080/retrieve automaticamente.
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
import uvicorn

load_dotenv()

# ─────────────────────────────────────────────
# Configuração
# ─────────────────────────────────────────────
PINECONE_API_KEY  = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX    = os.getenv("PINECONE_INDEX_NAME", "memoria")
EMBEDDING_MODEL   = "all-MiniLM-L6-v2"
TOP_K             = 5

# Mapeamento: palavra-chave na query → namespace
NAMESPACE_RULES = {
    "totvs"      : "work-context",
    "protheus"   : "work-context",
    "sql"        : "work-context",
    "datasul"    : "work-context",
    "fluig"      : "work-context",
    "topdesk"    : "work-context",
    "sharepoint" : "work-context",
    "erp"        : "work-context",
    "home lab"   : "home-context",
    "homelab"    : "home-context",
    "home-lab"   : "home-context",
    "proxmox"    : "home-context",
    "docker"     : "home-context",
    "lua"        : "home-context",
    "automação"  : "home-context",
    "automacao"  : "home-context",
    "mod"        : "home-context",
    "pessoal"    : "home-context",
    "javascript" : "home-context",
}
DEFAULT_NAMESPACE = "work-context"

# ─────────────────────────────────────────────
# Inicialização (carrega modelo uma vez só)
# ─────────────────────────────────────────────
print("⏳ Carregando modelo de embeddings...")
model = SentenceTransformer(EMBEDDING_MODEL)
print("✅ Modelo carregado.")

print("⏳ Conectando ao Pinecone...")
pc    = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)
print(f"✅ Conectado ao índice '{PINECONE_INDEX}'.")

app = FastAPI(title="Memória Context Provider")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def detect_namespace(query: str) -> str:
    """Detecta o namespace correto baseado em palavras-chave na query."""
    q = query.lower()
    for keyword, ns in NAMESPACE_RULES.items():
        if keyword in q:
            return ns
    return DEFAULT_NAMESPACE


def search_pinecone(query: str, namespace: str) -> list[dict]:
    vector  = model.encode(query).tolist()
    result  = index.query(
        vector=vector,
        top_k=TOP_K,
        namespace=namespace,
        include_metadata=True,
    )
    return result.matches


def format_for_continue(matches, namespace: str) -> list[dict]:
    """
    Formata os resultados no schema esperado pelo Continue.dev:
    [{ name, description, content }]
    """
    items = []
    for m in matches:
        meta    = m.metadata or {}
        source  = meta.get("source", m.id)
        text    = meta.get("text", "")
        score   = round(m.score, 4)

        items.append({
            "name"       : f"[{namespace}] {source}",
            "description": f"score: {score} | {source}",
            "content"    : text,
        })
    return items

# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────
@app.post("/retrieve")
async def retrieve(request: Request):
    """
    Endpoint principal consumido pelo Continue.dev.
    Recebe { query, fullInput } e retorna chunks relevantes do Pinecone.
    """
    body      = await request.json()
    query     = body.get("query") or body.get("fullInput", "")
    namespace = detect_namespace(query)

    print(f"\n🔍 Query     : {query}")
    print(f"   Namespace : {namespace}")

    matches = search_pinecone(query, namespace)
    results = format_for_continue(matches, namespace)

    print(f"   Resultados: {len(results)} chunks retornados")
    return results


@app.get("/health")
async def health():
    stats = index.describe_index_stats()
    return {
        "status"       : "ok",
        "index"        : PINECONE_INDEX,
        "total_vectors": stats.total_vector_count,
        "namespaces"   : list(stats.namespaces.keys()),
    }


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🚀 Memória Context Provider rodando em http://localhost:8080")
    print("   Mantenha este terminal aberto enquanto usa o VSCodium.\n")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="warning")
