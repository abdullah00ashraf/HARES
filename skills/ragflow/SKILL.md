---
name: ragflow
description: Deep document understanding, structured multi-template chunking, hybrid search (dense + BM25), and agent context retrieval using RAGFlow.
---

# /ragflow: Deep Document Understanding & Agent Context Engine

**RAGFlow** is an open-source RAG (Retrieval-Augmented Generation) engine based on deep document understanding. It fuses cutting-edge retrieval techniques with agent capabilities to create a superior context layer for LLMs.

Location: [`c:/Producttolaunch/.agents/RAG`](file:///c:/Producttolaunch/.agents/RAG)

---

## 1. Core Architectural Pillars

1. **Deep Document Understanding (DeepDoc)**:
   - Native OCR and layout extraction for complex PDFs, PPTXs, DOCXs, and scanned tables.
   - Extracts semantic reading order, tables, headers, and visual figures without destroying context.

2. **Template-Driven Chunking**:
   - `naive`: Standard sliding window with token bounds.
   - `qa`: FAQ and question-answering pairs.
   - `table`: Structured Excel/CSV/table extraction preserving column-row relationships.
   - `paper`: Academic paper structure (Abstract, Methodology, Results, References).
   - `book`: Hierarchical chapter/section decomposition.
   - `laws`: Legal clause, subsection, and statute boundary parsing.
   - `manual`: Technical manuals and step-by-step procedures.

3. **Hybrid Multi-Stage Retrieval**:
   - **Dense Vector Search**: Embedding similarity via cosine/dot-product.
   - **BM25 Keyword Search**: Full-text lexical search indexing terms, tokens, and acronyms.
   - **Cross-Encoder Reranking**: Reranks top-$K$ candidates to eliminate hallucinations.

4. **Agentic Context Layer**:
   - Programmatic Python SDK (`ragflow_sdk`) and REST API.
   - Dynamic canvas workflows, conversational memory, and citation attribution.

---

## 2. Python SDK Quickstart

The Python SDK is located at [`c:/Producttolaunch/.agents/RAG/sdk/python`](file:///c:/Producttolaunch/.agents/RAG/sdk/python):

```python
from ragflow_sdk import RAGFlow

# Initialize client (defaults to localhost:9380)
rag = RAGFlow(api_key="<YOUR_API_KEY>", base_url="http://127.0.0.1:9380")

# 1. Create or retrieve a knowledge base dataset
dataset = rag.create_dataset(name="Sovereign_Workspace_Docs", chunk_method="manual")

# 2. Upload and parse documents
doc = dataset.upload_document(display_name="Architecture_Brief.pdf", blob=open("Architecture_Brief.pdf", "rb").read())
dataset.parse_documents([doc.id])

# 3. Retrieve ground-truth context with citations
chunks = dataset.retrieve(
    question="How does the AI Tower arbitrate telemetry decisions?",
    top_k=5,
    similarity_threshold=0.75
)

for chunk in chunks:
    print(f"[{chunk.document_name}] Score: {chunk.similarity:.2f}\n{chunk.content}\n")
```

---

## 3. Server Deployment via Docker

To launch the RAGFlow backend server locally:

```powershell
cd "c:\Producttolaunch\.agents\RAG\docker"
docker compose up -d
```

The web dashboard is served at `http://localhost:80` (or configured port) and API at `http://localhost:9380`.

---

## 4. Master Orchestrator Integration

When routed through `/master-orchestrator`:
* Use `--subagent rag` to target document parsing and context retrieval.
* Combine with `/understand` to cross-reference conceptual knowledge graph nodes with raw document source citations.
