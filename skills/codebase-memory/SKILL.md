---
name: codebase-memory
description: Sub-millisecond code intelligence, AST knowledge graphs across 162 languages, and 17 MCP tools using codebase-memory-mcp.
---

# /codebase-memory: Sub-Millisecond Code Intelligence & MCP Knowledge Graph

**codebase-memory-mcp** is a high-performance code intelligence MCP server that indexes codebases into a persistent knowledge graph. It evaluates structural queries in under 1ms, supports 162 languages via compiled tree-sitter grammars and Hybrid LSP, uses 99% fewer tokens, and runs as a pure static binary with zero external dependencies.

Location: [`c:/Producttolaunch/.agents/memory`](file:///c:/Producttolaunch/.agents/memory)  
Runtime Binary: `C:/Users/abdul/.local/bin/codebase-memory-mcp.exe`  
MCP Config: `C:/Users/abdul/.gemini/config/mcp_config.json`

---

## 1. Core Architectural Capabilities

1. **Sub-Millisecond Queries**:
   - In-memory SQLite with fused Aho-Corasick and LZ4 compression.
   - Answers structural queries, symbol lookups, and call-hierarchy traces in sub-millisecond time.

2. **162 Languages & Hybrid LSP**:
   - Vendored tree-sitter parsers compiled into native C binary.
   - Hybrid LSP semantic type resolution for Python, TypeScript/JavaScript/JSX/TSX, PHP, C#, Go, C, C++, Java, Kotlin, Rust, and Perl.

3. **17 Model Context Protocol (MCP) Tools**:
   - Auto-configured for Antigravity IDE & CLI via `mcp_config.json`.
   - Accessible to agents as native tool calls (`index_repository`, `search_graph`, `query_graph`, `trace_path`, etc.).

4. **Interactive 3D Graph UI**:
   - Built-in visualizer served directly on `http://localhost:9749`.

---

## 2. 17 Available MCP Tools Reference

| Tool | Parameters | Description |
|---|---|---|
| `index_repository` | `path` | Indexes repository into persistent graph. |
| `search_graph` | `query`, `limit` | Search symbols, functions, classes, and types. |
| `query_graph` | `query` (Cypher) | Execute Cypher-like queries on the graph. |
| `trace_path` | `from`, `to` | Trace execution call paths between symbols. |
| `get_code_snippet` | `symbol`, `file` | Retrieve syntax-highlighted snippet with context. |
| `get_file_outline` | `path` | Hierarchical structural outline of source file. |
| `get_graph_schema` | *(none)* | Inspect graph node types and edge schemas. |
| `compare_graphs` | `base`, `head` | Diff two graph snapshots to find breaking changes. |
| `get_architecture` | *(none)* | High-level summary of modules, services, and edges. |
| `search_code` | `pattern`, `path` | Fast regex & text pattern matching. |
| `list_projects` | *(none)* | List all indexed projects in the workspace. |
| `delete_project` | `project_id` | Remove project cache and index. |
| `index_status` | *(none)* | Index progress, stats, and memory utilization. |
| `check_index_coverage`| *(none)* | Identify files omitted or unindexed. |
| `detect_changes` | *(none)* | Incremental changes detected since last run. |
| `manage_adr` | `action`, `title` | Create and query Architectural Decision Records. |
| `ingest_traces` | `traces` | Ingest dynamic runtime execution traces. |

---

## 3. Quick CLI Commands

```powershell
# Index a repository:
& "C:\Users\abdul\.local\bin\codebase-memory-mcp.exe" cli index_repository path="c:/Producttolaunch/managerAI"

# Search symbols:
& "C:\Users\abdul\.local\bin\codebase-memory-mcp.exe" cli search_graph query="Hydrology"

# Launch 3D Graph UI:
& "C:\Users\abdul\.local\bin\codebase-memory-mcp.exe" --ui=true --port=9749
```

---

## 4. Master Orchestrator Integration

When dispatched through `/master-orchestrator`:
* Use `--subagent memory` to trigger deep symbol and call graph searches.
* Cross-reference with `/understand` AST graphs (`graphs/`) and RAG context layers (`RAG/`) to achieve total architectural grounding with minimal token consumption.
