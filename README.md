# Memória: Knowledge Architect RAG

Sistema de gestão de conhecimento técnico dividido em dois contextos estritos: **[PROFISSIONAL]** e **[PESSOAL]**.

## 🏗️ Arquitetura
Este projeto utiliza:
- **GitHub**: Repositório central de conhecimento (Markdown e Código).
- **Pinecone**: Banco de dados vetorial para recuperação semântica (RAG).
- **GitHub Actions**: Pipeline automatizado para vetorização de novos documentos.
- **Local Embeddings**: Geração de vetores via `sentence-transformers` (Modelo: `paraphrase-multilingual-MiniLM-L12-v2`). **Custo: Zero.**

## 📁 Estrutura de Pastas
- `docs/professional/`: Conhecimento sobre ERP TOTVS, SQL Server, Office 365, etc.
- `docs/personal/`: Conhecimento sobre Home Lab, JavaScript, Lua, Python, etc.
- `scripts/`: Ferramentas de suporte e vetorização.
- `.github/workflows/`: Automação CI/CD para atualização do Pinecone.

## 🚀 Como Usar
1. Adicione arquivos `.md` ou `.py` na pasta `docs/`.
2. Ao fazer o `push`, o GitHub Actions irá gerar os embeddings e enviá-los ao Pinecone.
3. Utilize os metadados para filtrar suas consultas:
   - `namespace`: `work-context` ou `home-context`.
   - `category`: `pro` ou `personal`.

## 🛠️ Configuração
Certifique-se de configurar os seguintes Secrets no seu repositório GitHub:
- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME`

---
*Gerenciado por: Knowledge Architect RAG*
