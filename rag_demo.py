from dotenv import load_dotenv

load_dotenv()

import psycopg
from openai import OpenAI
from pgvector.psycopg import register_vector

from app.services.embedding_service import create_embedding

SIMILARITY_THRESHOLD = 0.50
TOP_K = 3

client = OpenAI()

query = "My laptop was stolen from my hotel room"

query_embedding = create_embedding(query)

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
            claim_text,
            1 - (embedding <=> %s::vector) AS similarity
        FROM claim_embeddings
        WHERE 1 - (embedding <=> %s::vector) >= %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """,
        (
            query_embedding,
            query_embedding,
            SIMILARITY_THRESHOLD,
            query_embedding,
            TOP_K,
        ),
    )

    retrieved_claims = cursor.fetchall()

connection.close()

if not retrieved_claims:
    print("\nNo sufficiently relevant historical claims found.")
    raise SystemExit

context_lines = []

for claim_text, similarity in retrieved_claims:
    context_lines.append(
        f"- {claim_text} (similarity: {similarity:.4f})"
    )

context = "\n".join(context_lines)


response = client.responses.create(
    model="gpt-5.4-mini",
    input=[
        {
            "role": "system",
            "content": (
                "You are assisting with insurance claim intake analysis. "
                "Use the retrieved historical claims as supporting context. "
                "Do not invent facts that are not present in the new claim or retrieved context. "
                "Explain how the retrieved claims relate to the new claim."
            ),
        },
        {
            "role": "user",
            "content": f"""
NEW CLAIM:
{query}

RETRIEVED HISTORICAL CLAIMS:
{context}

Provide:
1. A short summary of the new claim.
2. Which retrieved claim is most relevant and why.
3. Any useful pattern or risk signal suggested by the retrieved history.
""",
        },
    ],
)

print("\nNEW CLAIM:")
print(query)

print("\nRETRIEVED CONTEXT:")
print(context)

print("\nRAG RESPONSE:")
print(response.output_text)