import json
import math
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from app.services.embedding_service import create_embedding


INDEX_FILE = Path("claim_index.json")

claims = [
    "Basement flooded after heavy rain",
    "Water entered cellar during storm",
    "Rear bumper damaged in parking lot",
    "Kitchen pipe burst under sink",
]

query = "Storm caused water to enter my downstairs storage area"


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot_product = sum(x * y for x, y in zip(a, b))

    magnitude_a = math.sqrt(sum(x * x for x in a))
    magnitude_b = math.sqrt(sum(y * y for y in b))

    return dot_product / (magnitude_a * magnitude_b)


def build_index():
    records = []

    for claim in claims:
        print(f"Embedding historical claim: {claim}")

        records.append({
            "claim": claim,
            "embedding": create_embedding(claim),
        })

    INDEX_FILE.write_text(json.dumps(records))

    print(f"\nSaved {len(records)} embeddings to {INDEX_FILE}")


def load_index():
    return json.loads(INDEX_FILE.read_text())


if not INDEX_FILE.exists():
    print("No index found. Building one...\n")
    build_index()
else:
    print("Using existing claim index.")


records = load_index()

print(f"\nEmbedding query: {query}")
query_embedding = create_embedding(query)

results = []

for record in records:
    similarity = cosine_similarity(
        query_embedding,
        record["embedding"],
    )

    results.append((similarity, record["claim"]))

results.sort(key=lambda result: result[0], reverse=True)

print(f"\nQUERY: {query}\n")

for similarity, claim in results:
    print(f"{similarity:.4f}  {claim}")