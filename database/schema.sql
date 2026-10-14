-- Agentic RAG PostgreSQL schema
-- Compatible with backend/models.py
-- PostgreSQL + pgvector; embeddings use 768 dimensions (nomic-embed-text).
-- This script creates tables/indexes only; it does not create application users or insert documents.
-- Prefer running against a new/empty database. Review existing objects before importing into a populated DB.

BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(255),
    sha256 VARCHAR(64) NOT NULL,
    storage_path TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'uploaded',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(768),
    page_number INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_users_username ON users (username);
CREATE INDEX IF NOT EXISTS ix_documents_sha256 ON documents (sha256);
CREATE INDEX IF NOT EXISTS ix_document_chunks_document_id ON document_chunks (document_id);

-- HNSW index for cosine-distance vector retrieval (requires a recent pgvector version).
CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_hnsw
    ON document_chunks USING hnsw (embedding vector_cosine_ops);

COMMIT;

-- Verification:
-- SELECT extname FROM pg_extension WHERE extname = 'vector';
-- \dt
-- SELECT count(*) FROM users;
-- SELECT count(*) FROM documents;
-- SELECT count(*) FROM document_chunks;
