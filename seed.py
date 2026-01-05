import psycopg2
from psycopg2 import sql
import csv
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database connection configuration
# For demos we default to a local Postgres instance and read values from env vars
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    # disable SSL for local demo; set to 'require' when connecting to Supabase
    "sslmode": os.getenv("DB_SSLMODE", "disable")
}

def setup_schema(cur):
    """Enables extensions and creates the necessary database schema."""
    # Attempt to enable pgvector if available (harmless if not installed)
    pgvector_available = False
    try:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        pgvector_available = True
        print("pgvector extension enabled (if available)")
    except Exception:
        # ignore if extension can't be created in local/demo environment
        print("pgvector extension not available; using array type for embeddings")

    print("Creating tables if they don't exist...")
    if pgvector_available:
        embedding_type = 'vector(3)'
    else:
        embedding_type = 'real[]'

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            tier TEXT DEFAULT 'free' CHECK (tier IN ('free', 'pro')),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE TABLE IF NOT EXISTS embeddings (
            id SERIAL PRIMARY KEY,
            doc_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            embedding {embedding_type}
        );
    """)

def seed_from_csv(cur, file_path, doc_id):
    """
    Reads a CSV file and inserts the content into the embeddings table.
    Expected CSV format: content, v1, v2, v3
    """
    if not os.path.exists(file_path):
        print(f"Warning: CSV file not found at {file_path}. Skipping CSV seed.")
        return

    print(f"Reading data from {file_path}...")
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        # Skip header if it exists (uncomment if your CSV has a header row)
        # next(reader) 
        
        rows_to_insert = []
        for row in reader:
            if len(row) < 4:
                continue
            content = row[0]
            # Convert the numeric strings to a float list for pgvector
            vector = [float(row[1]), float(row[2]), float(row[3])]
            rows_to_insert.append((doc_id, content, vector))
        
        if rows_to_insert:
            cur.executemany(
                "INSERT INTO embeddings (doc_id, content, embedding) VALUES (%s, %s, %s)", 
                rows_to_insert
            )
            print(f"Successfully imported {len(rows_to_insert)} rows from CSV.")

def seed_database():
    conn = None
    try:
        print("Connecting to the PostgreSQL database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # 1. Setup Tables
        setup_schema(cur)

        # 2. Clear existing data
        print("Cleaning up existing data...")
        cur.execute("TRUNCATE users, documents, embeddings RESTART IDENTITY CASCADE;")

        # 3. Insert Sample Users
        print("Inserting sample users...")
        users = [
            (5, 'alice@example.com', 'pro'),
            (42, 'bob@hk-tech.edu', 'free')
        ]
        cur.executemany("INSERT INTO users (id, email, tier) VALUES (%s, %s, %s)", users)

        # 4. Insert Sample Documents
        print("Inserting sample documents...")
        docs = [
            (1, 42, 'Climate_Report.pdf'),
            (2, 5, 'AI_Ethics_v2.pdf'),
            (3, 5, 'DeepSeek_Architecture.pdf')
        ]
        cur.executemany("INSERT INTO documents (id, user_id, title) VALUES (%s, %s, %s)", docs)

        # 5. Insert Manual Mock Embeddings
        print("Inserting manual mock embeddings...")
        manual_embeddings = [
            (1, 'Global temperatures rose by 1.5 degrees...', [0.1, 0.9, 0.2]),
            (2, 'The alignment problem in LLMs refers to...', [0.7, 0.1, 0.8])
        ]
        cur.executemany("INSERT INTO embeddings (doc_id, content, embedding) VALUES (%s, %s, %s)", manual_embeddings)

        # 6. Insert from CSV (Optional Laboratory Step)
        # Assuming you have a file named 'data.csv' in the same folder
        seed_from_csv(cur, 'climate_report.csv', doc_id=1)
        seed_from_csv(cur, 'ai_ethics.csv', doc_id=2)
        seed_from_csv(cur, 'deepseek_architecture.csv', doc_id=3)

        conn.commit()
        print("Successfully seeded the database!")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
    finally:
        if conn is not None:
            cur.close()
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    # Ensure you have psycopg2 installed: pip install psycopg2-binary
    seed_database()