# Memória: Knowledge Architect RAG (Dual-Context)

Sistema de gestão de conhecimento técnico avançado com isolamento total entre contextos **[PROFISSIONAL]** (ERP TOTVS, SQL) e **[PESSOAL]** (Home Lab, Mods).

## 🏗️ Arquitetura
- **Ingestão**: `Crawl4AI` para extração de dados de alta fidelidade.
- **Vetorização**: `sentence-transformers` (Local/Free) para embeddings semânticos.
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
Copie o arquivo de exemplo e preencha suas chaves:
```bash
cp .env.example .env
```
> [!IMPORTANT]
> Nunca versione o arquivo `.env`. Ele já está bloqueado no `.gitignore`.

### 4. Uso
Adicione seus documentos em `docs/professional/` ou `docs/personal/` e execute o script de ingestão:
```bash
python scripts/vectorize.py --path docs
```

## 🛡️ Governança
Este projeto utiliza a **Golden Rule**: Jamais misturar contextos de busca para evitar alucinações profissionais com dados pessoais.

---
*Senior DevOps & Security Architect Baseline*
