# APIs We Want for Now

This document defines the **full API surface** for the app right now. No new endpoints are added; this is the set we keep and how they fit together.

---

## 1. Base / health

| Method | Path     | Purpose                                                                    |
|--------|----------|-----------------------------------------------------------------------------|
| **GET** | `/base/` | Sanity / health: returns `app_name`, `app_version`, and a welcome message. |

**Role:** Quick check that the app is up. Keep as-is.

---

## 2. Data APIs (prefix `/api/v1/data`)

| Method   | Path                                 | Purpose                                                                                                                                                                         |
|----------|--------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **GET**  | `/api/v1/data/pmc`                   | List available PMC doc_ids (from `pmc_articles/*.json` on disk). Returns `{"doc_ids": ["id1", ...]}`.                                                                          |
| **POST** | `/api/v1/data/upload/{project_id}`   | Upload a file (PDF/txt) into a project. Returns `signal` and `file_id`.                                                                                                        |
| **POST** | `/api/v1/data/process/{project_id}`  | Chunk an **already uploaded** file by `file_id`. Body: `ProcessRequest` (file_id, chunk_size, overlap_size). Returns list of chunks (same shape: page_content, metadata, type). |
| **POST** | `/api/v1/data/process_pmc_article`  | Chunk a **PMC article** by `doc_id`. Body: `PmcProcessRequest` (doc_id, chunk_size, overlap_size). Returns list of chunks (same shape).                                          |
| **POST** | `/api/v1/data/process_pmc_articles` | Chunk **multiple** PMC articles. Body: `BatchPmcProcessRequest` (doc_ids, chunk_size, overlap_size). Returns `{"results": [{"doc_id", "chunks"} or {"doc_id", "error"}]}`.     |
| **POST** | `/api/v1/data/ingest_pmc_article`   | Chunk one PMC article → embed → write to vector DB. Body: `IngestPmcRequest` (doc_id, collection_name, chunk_size, overlap_size). Uses config for LLM/Vector DB provider and embedding model. Returns `doc_id`, `collection_name`, `chunks_ingested`. |
| **POST** | `/api/v1/data/search`               | Semantic search. Body: `SearchRequest` (collection_name, query, limit). Returns `chunks` (text, metadata, score). Uses config embedding model. |
| **POST** | `/api/v1/data/query`                | RAG query. Body: `QueryRequest` (collection_name, query, limit). Returns `answer` and `chunks_used`. Uses config embedding and generation model. |

**Roles:**

- **GET /pmc:** List available PMC doc_ids so clients or pipelines know what can be chunked (disk today; later Mongo).
- **Upload + process (project):** Use when you have project-based file uploads (PDF/txt) and want to chunk them. If you never upload project files, you can ignore these two; they stay in the API for flexibility.
- **process_pmc_article:** Core for PMC flow. Today it loads the article from **JSON on disk** (`pmc_articles/{doc_id}.json`). Later we keep **this same API** and add a Mongo backend: same endpoint, same request/response; only the source of the article changes (Mongo instead of file). So one API for chunking PMC whether the doc lives on disk or in Mongo.
- **process_pmc_articles:** Batch chunking; one bad doc_id returns an error entry in results without failing the whole request.
- **ingest_pmc_article:** Single-call ingest: chunk → embed (via configured LLM) → create collection if needed → insert into configured vector DB.
- **search:** Semantic search over a collection; embed query and return top chunks (text, metadata, score).
- **query:** RAG: same as search, then generate an answer from retrieved chunks using the configured generation model.

---

## 3. Summary

- **9 endpoints total:** 1 GET base, 1 GET pmc (list doc_ids), 7 POST (upload, process project, process PMC, process PMC batch, ingest PMC, search, query).
- **Unified chunk response:** Process endpoints return the same structure (page_content, metadata, type; no id). Any consumer (embedder, vector DB pipeline) can treat them the same.
- **Single PMC chunking API:** `POST /api/v1/data/process_pmc_article` is the only endpoint for "chunk a single PMC article by id." Batch is `process_pmc_articles`; full ingest is `ingest_pmc_article`.

---

## 4. Out of scope for now (future only)

- Any new route or change to existing routes beyond the above.

This specification aligns with disk-backed PMC today and Mongo-backed PMC later.
