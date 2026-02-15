# Intended Data Flow

This document describes the intended data flow and architecture so that future work (MongoDB, other vector DBs) stays aligned.

- **Scraped data** can be stored in **MongoDB** (raw) or currently in JSON files under `pmc_articles/`. The application is designed to support both: a `PaperRepository` abstraction allows swapping storage (e.g. a future `MongoPaperRepository` for raw scraped papers).

- **Chunking** is done by the existing process endpoints (`POST /api/v1/data/process/{project_id}` for uploaded files, `POST /api/v1/data/process_pmc_article` for PMC JSON articles) or equivalent logic. Both endpoints return a **unified chunk shape**: each item has `page_content`, `metadata`, and `type` (no `id` field), so any downstream consumer sees the same structure.

- **Embedding and vector storage**: Chunks can be embedded using the LLM store (e.g. OpenAI or CoHere provider) and stored in **any vector DB** via the `VectorDBInterface`. The codebase uses a single abstraction for vector storage (e.g. Qdrant today; other implementations can be added behind the same interface without changing routes or services).

**End-to-end flow (current and planned):**

1. **Scrape** → store raw in MongoDB (planned) or in `pmc_articles/` JSON (current).
2. **Chunk** → via process endpoints or batch job reading from Mongo/JSON; output is the unified chunk list.
3. **Embed** → LLM store (embedding model).
4. **Store** → Vector DB via `VectorDBInterface` (Qdrant or another implementation).

No single vector DB or storage backend is hardcoded into the API; interfaces and factories allow swapping implementations.
