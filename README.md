# AI Research Assistant Database - Week 07

Local PostgreSQL + pgvector setup for semantic search demonstrations.

## Prerequisites

- Docker & Docker Compose
- Python 3.8+
- Git

## Quick Start

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `psycopg2-binary` — PostgreSQL connector
- `Flask` — web framework
- `python-dotenv` — environment variable management

### 2. Start local PostgreSQL with pgvector

```bash
docker compose pull
docker compose up -d
```

This launches Postgres on `localhost:5432` with the `ankane/pgvector` image (includes pgvector extension pre-installed).

### 3. Seed the database

The `.env` file automatically provides connection details:

```bash
python seed.py
```

This will:
- Enable the pgvector extension
- Create `users`, `documents`, and `embeddings` tables
- Insert sample data (2 users, 3 documents, 2 embeddings)
- Optionally load CSV files: `climate_report.csv`, `ai_ethics.csv`, `deepseek_architecture.csv`

### 4. Start the web dashboard

```bash
python app.py
```

Then open your browser to `http://localhost:5000`

## Environment Configuration

The `.env` file stores database credentials (do not commit to version control):

```
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=postgres
DB_SSLMODE=disable
```

Both `seed.py` and `app.py` automatically load these via `python-dotenv`.

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    tier TEXT DEFAULT 'free' CHECK (tier IN ('free', 'pro')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Documents Table
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Embeddings Table
```sql
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    doc_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(3)  -- Uses pgvector type for 3D vectors
);
```

## Python Scripts

### seed.py

Populates the database with schema and sample data.

**Functions:**

- **`setup_schema(cur)`** — Creates tables and enables pgvector extension
  - Detects pgvector availability and uses `vector(3)` or `real[]` accordingly
  
- **`seed_from_csv(cur, file_path, doc_id)`** — Reads CSV and inserts embeddings
  - Expected CSV format: `content, v1, v2, v3` (space/comma-separated vectors)
  - Skips rows with fewer than 4 columns
  
- **`seed_database()`** — Main orchestrator
  - Connects to DB
  - Sets up schema
  - Inserts 2 sample users, 3 sample documents, 2 sample embeddings
  - Optionally loads from CSV files

**Usage:**
```bash
python seed.py
```

### app.py

Flask web application with semantic search functionality.

**Routes:**

- **`GET /`** — Home page
  - Displays all users, documents, and embeddings in styled tables
  - Shows database statistics (counts)

- **`POST /search`** — Semantic search
  - Accepts a 3D query vector (e.g., `0.15 0.85 0.15`)
  - Returns top 10 embeddings ranked by similarity using pgvector's `<=>` operator
  - Similarity score: 1.0 = identical, 0.0 = opposite

- **`GET /api/stats`** — JSON endpoint
  - Returns database statistics: user count, document count, embedding count

**Key Functions:**

- **`get_db_connection()`** — Creates database connection using `.env` variables

- **`index()`** — Renders home page with all data

- **`search()`** — Handles semantic search
  - Parses query vector (space or comma-separated)
  - Casts to pgvector type with `::vector`
  - Returns ranked results by similarity

- **`stats()`** — Returns JSON stats

**Usage:**
```bash
python app.py
# Visit http://localhost:5000
```

## Web Dashboard Features

### Home Page (`/`)
- **User Statistics** — card display showing totals
- **Users Table** — ID, email, tier (free/pro)
- **Documents Table** — ID, user ID, title, upload date
- **Embeddings Table** — ID, doc ID, content preview, vector values

### Semantic Search Page (`/search`)
- **Vector Input Form** — enter 3D vectors (space or comma-separated)
- **Example Queries:**
  - `0.15 0.85 0.15` — Climate/temperature domain
  - `0.7 0.1 0.8` — AI/alignment domain
  - `0.9 0.2 0.4` — Architecture/efficiency domain
- **Results** — ranked by similarity (1.0 = best match)
- **Error Handling** — validates vector dimensions and format

## Docker Compose

### Default (with pgvector build)
```bash
docker compose up -d
```
Uses `Dockerfile-db` to build Postgres with pgvector from source (slower, ~5-10 min).

### Fast (no pgvector build)
```bash
docker compose -f docker-compose.nopgvector.yml up -d
```
Uses official `postgres:15` image (faster, but no pgvector).

### Recommended
```bash
docker compose -f docker-compose.yml up -d
```
Uses prebuilt `ankane/pgvector:latest` image (fast + pgvector included).

## Troubleshooting

**"Connection refused" error:**
```bash
docker ps | grep postgres
docker logs <container-id>
```

**pgvector operator error (`<=>`):**
Ensure the container is using `ankane/pgvector` image. Recreate:
```bash
docker compose down -v
docker compose up -d
python seed.py
```

**Vector dimension mismatch:**
Query vectors must have exactly 3 dimensions to match the `vector(3)` column type.

**CSV import fails:**
Verify CSV format (4 columns: content, v1, v2, v3). Check file path in `seed.py`.

## Next Steps (Week 07+)

- Replace mock 3D vectors with real 1536-dim embeddings from:
  - OpenAI text-embedding-3-small
  - Qwen-2.5 embeddings
  - BGE-Small
- Integrate n8n workflows for real-time embedding generation
- Add user authentication to Flask app
- Expand to semantic search across multiple documents

## Files Overview

- **seed.py** — Database initialization & population
- **app.py** — Flask web application
- **.env** — Environment variables (not committed)
- **docker-compose.yml** — Postgres with pgvector (prebuilt image)
- **docker-compose.nopgvector.yml** — Postgres only (no pgvector)
- **Dockerfile-db** — (Optional) build Postgres + pgvector from source
- **templates/index.html** — Home page template
- **templates/search.html** — Semantic search template
- **requirements.txt** — Python dependencies

## License

For educational purposes - Week 07 AI Course

