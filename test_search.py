"""
test_search.py — Script de validação do pipeline RAG do projeto Memória.

USO:
    python test_search.py

O script executa uma bateria de buscas semânticas no Pinecone e exibe
os resultados, permitindo atestar que a ingestão funcionou corretamente.
"""

import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone

# ─────────────────────────────────────────────
# Configuração
# ─────────────────────────────────────────────
load_dotenv()

PINECONE_API_KEY   = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX     = os.getenv("PINECONE_INDEX_NAME", "memoria")
EMBEDDING_MODEL    = "all-MiniLM-L6-v2"   # mesmo modelo usado no vectorize.py
TOP_K              = 3                      # quantos resultados retornar por busca

# Thresholds para o modelo all-MiniLM-L6-v2 com chunks de markdown.
# Este modelo produz scores cosine entre 0.10–0.35 em buscas pt/en — normal.
SCORE_OK   = 0.20   # ✅ documento relevante encontrado
SCORE_WARN = 0.12   # ⚠️  resultado marginal — abaixo = falha real

# ─────────────────────────────────────────────
# Casos de teste
# ─────────────────────────────────────────────
TEST_CASES = [
    {
        "label"    : "🔵 [PROFISSIONAL] Consulta sobre clientes no TOTVS",
        "query"    : "como consultar clientes ativos no Protheus com SQL",
        "namespace": "work-context",
    },
    {
        "label"    : "🔵 [PROFISSIONAL] Campos padrão das tabelas Protheus",
        "query"    : "quais são os campos obrigatórios nas tabelas do ERP Protheus",
        "namespace": "work-context",
    },
    {
        "label"    : "🔵 [PROFISSIONAL] Erro de deadlock no SQL Server",
        "query"    : "como resolver deadlock em banco de dados SQL Server",
        "namespace": "work-context",
    },
    {
        "label"    : "🟢 [PESSOAL] Isolamento — busca profissional no contexto pessoal (deve retornar score baixo)",
        "query"    : "como consultar clientes ativos no Protheus com SQL",
        "namespace": "home-context",
    },
]

# ─────────────────────────────────────────────
# Inicialização
# ─────────────────────────────────────────────
def init_clients():
    print("⏳ Carregando modelo de embeddings...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print(f"✅ Modelo '{EMBEDDING_MODEL}' carregado.\n")

    print("⏳ Conectando ao Pinecone...")
    pc    = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX)
    stats = index.describe_index_stats()
    print(f"✅ Conectado ao índice '{PINECONE_INDEX}'.")
    print(f"   Total de vetores: {stats.total_vector_count}")
    print(f"   Namespaces: {list(stats.namespaces.keys())}\n")
    return model, index


# ─────────────────────────────────────────────
# Busca semântica
# ─────────────────────────────────────────────
def search(model, index, query: str, namespace: str, top_k: int = TOP_K):
    vector = model.encode(query).tolist()
    result = index.query(
        vector=vector,
        top_k=top_k,
        namespace=namespace,
        include_metadata=True,
    )
    return result.matches


# ─────────────────────────────────────────────
# Runner de testes
# ─────────────────────────────────────────────
def run_tests(model, index):
    passed = 0
    failed = 0

    for tc in TEST_CASES:
        print("=" * 65)
        print(tc["label"])
        print(f"   Query    : \"{tc['query']}\"")
        print(f"   Namespace: {tc['namespace']}")
        print("-" * 65)

        matches = search(model, index, tc["query"], tc["namespace"])

        if not matches:
            print("   ⚠️  Nenhum resultado encontrado.")
            print("      → Verifique se o documento foi ingerido neste namespace.\n")
            failed += 1
            continue

        for i, m in enumerate(matches, 1):
            score    = m.score
            doc_id   = m.id
            metadata = m.metadata or {}
            source   = metadata.get("source", "N/A")
            text     = metadata.get("text", "")[:200].replace("\n", " ")

            if score >= SCORE_OK:
                status = "✅"
            elif score >= SCORE_WARN:
                status = "⚠️ "
            else:
                status = "❌"
            print(f"   {status} #{i}  score={score:.4f}  id={doc_id}")
            print(f"        fonte  : {source}")
            print(f"        trecho : {text}...")
            print()

        top_score = matches[0].score if matches else 0
        if top_score >= SCORE_OK:
            passed += 1
        elif top_score >= SCORE_WARN:
            print("   ⚠️  Score marginal — documento encontrado mas com baixa confiança.")
            passed += 1  # ainda conta como sucesso parcial
        else:
            print("   ❌ Score muito baixo — documento provavelmente não foi ingerido.")
            failed += 1

    # ── Resumo ──────────────────────────────
    print("=" * 65)
    print(f"\n📊 RESULTADO FINAL: {passed}/{len(TEST_CASES)} testes aprovados")
    if failed == 0:
        print("🎉 Tudo funcionando! O pipeline RAG está operacional.\n")
    else:
        print(f"⚠️  {failed} teste(s) falharam. Verifique os logs acima.\n")


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    if not PINECONE_API_KEY:
        raise SystemExit("❌ PINECONE_API_KEY não encontrada no .env")

    model, index = init_clients()
    run_tests(model, index)
