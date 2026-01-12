import os
import psycopg2
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Database connection configuration
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "sslmode": os.getenv("DB_SSLMODE", "disable")
}

def get_db_connection():
    """Create and return a database connection."""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    return conn

@app.route('/')
def index():
    """Display overview of database contents."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Fetch users
        cur.execute("SELECT id, email, tier FROM users ORDER BY id;")
        users = cur.fetchall()
        
        # Fetch documents
        cur.execute("SELECT id, user_id, title, upload_date FROM documents ORDER BY id;")
        documents = cur.fetchall()
        
        # Fetch embeddings
        cur.execute("SELECT id, doc_id, content, embedding FROM embeddings ORDER BY id;")
        embeddings = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('index.html', users=users, documents=documents, embeddings=embeddings)
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p>", 500

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Semantic search using pgvector."""
    results = None
    query_vector = None
    error = None
    
    if request.method == 'POST':
        try:
            # Parse the query vector from form input
            query_input = request.form.get('query_vector', '').strip()
            if not query_input:
                error = "Please enter a query vector."
            else:
                # Parse space or comma-separated values
                query_vector = [float(x.strip()) for x in query_input.replace(',', ' ').split()]
                
                if len(query_vector) != 3:
                    error = "Query vector must have exactly 3 dimensions."
                else:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    
                    # Perform semantic search using pgvector operator (<=>)
                    # Cast the query vector to vector type for pgvector compatibility
                    query = """
                        SELECT id, doc_id, content, embedding, 1 - (embedding <=> %s::vector) AS similarity
                        FROM embeddings
                        ORDER BY similarity DESC
                        LIMIT 10;
                    """
                    cur.execute(query, (query_vector,))
                    results = cur.fetchall()
                    
                    cur.close()
                    conn.close()
        except ValueError as ve:
            error = f"Invalid vector format: {str(ve)}"
        except Exception as e:
            error = f"Database error: {str(e)}"
    
    return render_template('search.html', results=results, query_vector=query_vector, error=error)

@app.route('/api/stats')
def stats():
    """Return database stats as JSON."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM users;")
        user_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM documents;")
        doc_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM embeddings;")
        embed_count = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return jsonify({
            "users": user_count,
            "documents": doc_count,
            "embeddings": embed_count
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
