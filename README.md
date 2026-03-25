# Memória: Knowledge Architect RAG (Dual-Context)

Sistema de gestão de conhecimento técnico avançado com isolamento total entre contextos **[PROFISSIONAL]** (ERP TOTVS, SQL) e **[PESSOAL]** (Home Lab, Mods).

## 🏗️ Arquitetura
- **Ingestão**: Leitura local (`.md`, `.py`) e web scraping dinâmico via `Crawl4AI`.
- **Vetorização**: `sentence-transformers` (Local/Free) utilizando o modelo `paraphrase-multilingual-MiniLM-L12-v2`.
- **Armazenamento**: `Pinecone` utilizando **Namespaces** para separação de contextos.
- **Segurança**: Governança via `.env`, hooks de pré-commit e histórico Git auditado.

## 🚀 Instalação e Configuração

### 1. Pré-requisitos
- Python 3.10+
- Pinecone Account (Free Tier)

### 2. Instalação
Clone o repositório e instale as dependências:
```bash
pip install -r requirements.txt
python -m playwright install chromium
```

### 3. Configuração do Ambiente

**Local:**
Copie o arquivo de exemplo e preencha suas chaves:
```bash
cp .env.example .env
```

**GitHub (Dashboard e Automação):**
Para que o Dashboard e as Actions funcionem, adicione os seguintes **Secrets** no repositório (Settings > Secrets > Actions):
- `PINECONE_API_KEY`: Sua chave do Pinecone.
- `PINECONE_INDEX_NAME`: O nome do seu índice (ex: `memoria`).

**Ativando o Dashboard (GitHub Pages):**
1. Vá em **Settings > Pages**.
2. Escolha a branch `main`.
3. O painel ficará em `https://seu-usuario.github.io/memoria`.

### 4. Uso

**Ingestão de Arquivos Locais:**
```bash
python scripts/vectorize.py --path docs
```

**Ingestão Web (Crawl4AI):**
```bash
python scripts/crawl_ingest.py "https://url.com" --context pro --depth 1 --limit 10
```
- `--depth`: Nível de navegação (1 = apenas a página, 2+ = segue links internos).
- `--limit`: Máximo de páginas a serem capturadas.

**💡 Recurso: Limpeza Automática**
O sistema possui **Upsert Inteligente**. Ao re-ingerir a mesma URL ou arquivo, ele apaga automaticamente os vetores antigos daquela fonte antes de inserir os novos, garantindo que não haja dados duplicados ou obsoletos.

## 🛡️ Governança
Este projeto utiliza a **Golden Rule**: Jamais misturar contextos de busca para evitar alucinações profissionais com dados pessoais.

---
*Senior DevOps & Security Architect Baseline*
