from pathlib import Path


SCHEMA_PATH = Path(__file__).resolve().parents[2] / "database" / "schema.sql"


def test_schema_sql_matches_core_agentic_rag_tables():
    sql = SCHEMA_PATH.read_text(encoding="utf-8").lower()
    assert "create extension if not exists vector" in sql
    assert "create table if not exists users" in sql
    assert "create table if not exists documents" in sql
    assert "create table if not exists document_chunks" in sql
    assert "embedding vector(768)" in sql
    assert "references documents(id) on delete cascade" in sql


def test_schema_sql_has_vector_search_index_and_safe_defaults():
    sql = SCHEMA_PATH.read_text(encoding="utf-8").lower()
    assert "using hnsw (embedding vector_cosine_ops)" in sql
    assert "metadata jsonb not null default '{}'::jsonb" in sql
    assert "password_hash varchar(255) not null" in sql
