from dotenv import load_dotenv

load_dotenv()

import psycopg
from pgvector.psycopg import register_vector

from app.services.embedding_service import create_embedding

claims = [
    "Basement flooded after heavy rain",
    "Water entered cellar during storm",
    "Rear bumper damaged in parking lot",
    "Kitchen pipe burst under sink",
]


connection = psycopg.connect(
    host="localhost",
    port=5432,
    dbname="ai_intake",
    user="aiuser",
    password="aipassword",
)

register_vector(connection)

with connection.cursor() as cursor:
    for claim in claims:
        print(f"Embedding: {claim}")

        embedding = create_embedding(claim)

        cursor.execute(
            """
            INSERT INTO claim_embeddings (claim_text, embedding)
            VALUES (%s, %s)
            """,
            (claim, embedding),
        )

connection.commit()
connection.close()

print("Done.")