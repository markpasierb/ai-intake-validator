from dotenv import load_dotenv

load_dotenv()

import psycopg
from pgvector.psycopg import register_vector

from app.services.embedding_service import create_embedding


query = "Car hit while parked at the grocery store"

query_embedding = create_embedding(query)

vector_sql = "[" + ",".join(str(value) for value in query_embedding) + "]"

print("\nCOPY/PASTE SQL:\n")
print(f"""
SELECT
    id,
    claim_text,
    1 - (embedding <=> '{vector_sql}'::vector) AS similarity
FROM claim_embeddings
ORDER BY embedding <=> '{vector_sql}'::vector
LIMIT 4;
""")

connection = psycopg.connect(
    host="localhost",
    port=5432,
    dbname="ai_intake",
    user="aiuser",
    password="aipassword",
)

register_vector(connection)

with connection.cursor() as cursor:
    cursor.execute(
        """
        SELECT
            id,
            claim_text,
            1 - (embedding <=> %s::vector) AS similarity
        FROM claim_embeddings
        ORDER BY embedding <=> %s::vector
        LIMIT 4
        """,
        (query_embedding, query_embedding),
    )

    results = cursor.fetchall()

connection.close()

print(f"\nQUERY: {query}\n")

for claim_id, claim_text, similarity in results:
    print(
        f"{similarity:.4f}  "
        f"{claim_id}: {claim_text}"
    )