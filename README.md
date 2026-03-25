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
```

### 3. Configuração do Ambiente

**Local:**
Copie o arquivo de exemplo e preencha suas chaves:
```bash
cp .env.example .env
```

**GitHub (Para Dashboard e Automação):**
Para que o Dashboard e as Actions funcionem, você deve adicionar os seguintes **Secrets** no seu repositório (Settings > Secrets and variables > Actions):
- `PINECONE_API_KEY`: Sua chave do Pinecone.
- `PINECONE_INDEX_NAME`: O nome do seu índice (ex: `memoria`).

**Ativando o Dashboard (GitHub Pages):**
1. Vá em **Settings > Pages**.
2. Em "Build and deployment", escolha a branch `main` (ou a sua branch principal).
3. Salve e aguarde alguns minutos. O painel estará disponível em `https://seu-usuario.github.io/memoria`.

### 4. Uso

**Ingestão de Arquivos Locais:**
Adicione seus documentos em `docs/professional/` ou `docs/personal/` e execute:
```bash
python scripts/vectorize.py --path docs
```

**Ingestão Web (Crawl4AI):**
Para capturar conteúdo diretamente de uma URL:
```bash
python scripts/crawl_ingest.py "https://url-do-site.com" --context pro
```
*(Use `--context personal` para o contexto pessoal)*

## 🛡️ Governança
Este projeto utiliza a **Golden Rule**: Jamais misturar contextos de busca para evitar alucinações profissionais com dados pessoais.

---
*Senior DevOps & Security Architect Baseline*
