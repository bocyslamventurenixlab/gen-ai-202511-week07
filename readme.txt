Project Setup & Database Guide

This repository includes a small demo app that uses a PostgreSQL database with embeddings. The README below explains two ways to run the database:

- Cloud (Supabase): quick, includes pgvector by default.
- Local (Docker): use the provided docker-compose files for a fast local demo.

Prerequisites

- Docker (for local demo)
- Python 3.8+
- Recommended Python deps: see requirements.txt (psycopg2-binary)

Quick Start — Local (fast, no pgvector build)

1. Start the official Postgres container (no pgvector build):

```bash
cd /workspaces/gen-ai-202511-week07
docker compose -f docker-compose.nopgvector.yml up -d
```

2. Export demo environment variables:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_NAME=postgres
export DB_SSLMODE=disable
```

3. Install Python deps and run the seeder:

```bash
pip install -r requirements.txt
python seed.py
```

Quick Start — Local with pgvector (optional, longer build)

If you want pgvector available in the DB (closer to Supabase), use the provided Dockerfile-db which builds Postgres and installs pgvector. This can fail in some restricted environments and takes longer.

```bash
docker compose build
docker compose up -d
```

If the build fails (network or build toolchain issues), use the `docker-compose.nopgvector.yml` file above instead.

Using Supabase (Cloud)

If you prefer Supabase, get the connection details from Project Settings → Database → Connection string. In production/demo you should set environment variables instead of hardcoding credentials:

```bash
export DB_HOST=your-supabase-host
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD="<your-password>"
export DB_NAME=postgres
export DB_SSLMODE=require
```

Schema and Seed Data

The seeder (`seed.py`) creates these tables when run: `users`, `documents`, `embeddings`.

- For local demos the `embedding` column uses `real[]` to avoid requiring `pgvector`.
- On Supabase (or a Postgres with pgvector) the `embedding` column can be `vector(3)` instead.

If you prefer manual SQL, these are the core statements used by the seeder:

```sql
-- Enable vector extension (Supabase or pgvector-enabled DB)
CREATE EXTENSION IF NOT EXISTS vector;

-- Tables
CREATE TABLE users (id SERIAL PRIMARY KEY, email TEXT UNIQUE NOT NULL, tier TEXT DEFAULT 'free', created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());
CREATE TABLE documents (id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, title TEXT NOT NULL, upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW());
-- For pgvector-enabled DB use: embedding vector(3)
-- For local demo use: embedding real[]
CREATE TABLE embeddings (id SERIAL PRIMARY KEY, doc_id INTEGER REFERENCES documents(id) ON DELETE CASCADE, content TEXT NOT NULL, embedding real[]);

-- Sample rows (same data the seeder inserts)
INSERT INTO users (id, email, tier) VALUES (5, 'alice@example.com', 'pro'), (42, 'bob@hk-tech.edu', 'free');
INSERT INTO documents (id, user_id, title) VALUES (1, 42, 'Climate_Report.pdf'), (2, 5, 'AI_Ethics_v2.pdf'), (3, 5, 'DeepSeek_Architecture.pdf');
INSERT INTO embeddings (doc_id, content, embedding) VALUES (1, 'Global temperatures rose by 1.5 degrees...', ARRAY[0.1,0.9,0.2]), (1, 'Arctic ice levels are at a record low.', ARRAY[0.2,0.8,0.1]), (2, 'The alignment problem in LLMs refers to...', ARRAY[0.7,0.1,0.8]);
```

Verification — Semantic Search Example

On a pgvector-enabled database you can run:

```sql
SELECT content, 1 - (embedding <=> '[0.15, 0.85, 0.15]') AS similarity
FROM embeddings
ORDER BY similarity DESC
LIMIT 2;
```

On the local demo (using `real[]`) you can run a simple similarity test in SQL or compute similarity in Python after fetching vectors.

Security Note

- Never commit real passwords or secrets to git. Use environment variables or a secrets manager.

Troubleshooting

- If the DB container shows `Connection refused`, run `docker ps` and `docker logs <container>` to inspect startup errors.
- If the `docker compose build` step fails building `pgvector`, use `docker-compose.nopgvector.yml` for a fast local demo.

Next Steps

In Week 07 we'll replace these mock vectors with real model embeddings (1536d) and add semantic search code.
