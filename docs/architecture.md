# Architecture: Dual-Context RAG

## 🧩 Architectural Overview
This project implements a Dual-Context RAG (Retrieval-Augmented Generation) system designed to manage two distinct knowledge bases with zero cross-contamination.

### 1. Dual-Context Isolation
The core principle of this architecture is the use of **Namespaces** to prevent "professional hallucinations" with personal data.

- **Namespace: `work-context`**
  - Profile: SysAdmin / Systems Analyst.
  - Domains: ERP TOTVS (Datasul, Fluig), ITSM (TOPDesk), SQL Server Administration, Office 365/SharePoint.
- **Namespace: `home-context`**
  - Profile: Home Lab / Developer.
  - Domains: Protocolo V, Mods Project Zomboid, Home Automation, Python/Lua experimentation.

> **💡 The Golden Rule**: Jamais misturar contextos de busca para evitar alucinações profissionais com dados pessoais.

## 🚀 Ingestion Flow
The pipeline is designed for high-fidelity data extraction and semantic retrieval:

1. **Extraction (`Crawl4AI`)**: Crawling and scraping web-based or local documentation.
2. **Chunking**: Dividing documents into manageable semantic units.
3. **Embedding**: Converting text to vectors using local `sentence-transformers` (Free) or OpenAI.
4. **Vector Store (`Pinecone`)**: Storing vectors into specific namespaces based on the source path.

## 🛡️ Security Governance
- **Git Purge**: Historical `.env` files have been purged from the repository.
- **Local Env**: All sensitive keys must reside in a local-only `.env` file.
- **Secret Detection**: Pre-commit hooks are configured to block commits containing sensitive strings.
