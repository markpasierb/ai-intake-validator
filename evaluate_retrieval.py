from dotenv import load_dotenv

load_dotenv()

import psycopg
from pgvector.psycopg import register_vector
from openai import OpenAI

from app.services.embedding_service import create_embedding


client = OpenAI()


TEST_CASES = [
    # Clear positives
    {
        "query": "Kitchen leak under sink caused water damage to cabinets and flooring",
        "expected_ids": [4],
    },
    {
        "query": "Car hit while parked at the grocery store",
        "expected_ids": [3],
    },
    {
        "query": "Storm caused water to enter my downstairs storage area",
        "expected_ids": [2],
    },

    # Clear negatives
    {
        "query": "My laptop was stolen from my hotel room",
        "expected_ids": [],
    },
    {
        "query": "My car was stolen from a parking garage",
        "expected_ids": [],
    },

    # Negation / no-loss traps
    {
        "query": "The basement was inspected after a storm and no water entered the house",
        "expected_ids": [],
    },
    {
        "query": "There was a leak under the sink but no damage occurred",
        "expected_ids": [],
    },
    {
        "query": "A vehicle nearly hit my parked car but there was no contact or damage",
        "expected_ids": [],
    },

    # Maintenance / preventive work
    {
        "query": "The plumber replaced an aging pipe under the kitchen sink before it failed",
        "expected_ids": [],
    },
    {
        "query": "Basement waterproofing was installed as preventive maintenance",
        "expected_ids": [],
    },

    # Similar subject, different event
    {
        "query": "Heavy rain damaged the roof but the basement remained dry",
        "expected_ids": [],
    },
    {
        "query": "A kitchen fire damaged the cabinets near the sink",
        "expected_ids": [],
    },
    {
        "query": "The front windshield was cracked while the car was parked",
        "expected_ids": [],
    },

    # Hard positives with different wording
    {
        "query": "A plumbing failure beneath the kitchen counter soaked the surrounding cabinetry",
        "expected_ids": [4],
    },
    {
        "query": "Rainwater came into the lower level of the house during a severe storm",
        "expected_ids": [2],
    },
    {
        "query": "Another vehicle struck the back of my unattended car in a parking area",
        "expected_ids": [3],
    },

    # Ambiguous / tricky
    {
        "query": "Water was discovered under the kitchen sink and the cabinet base was swollen",
        "expected_ids": [4],
    },
    {
        "query": "The basement smelled damp after heavy rain but no visible water damage was found",
        "expected_ids": [],
    },
    {
        "query": "My parked car had fresh damage on the rear bumper when I returned",
        "expected_ids": [3],
    },
    {
        "query": "A storm knocked out power and spoiled food in the basement freezer",
        "expected_ids": [],
    },
]


HOLDOUT_CASES = [
    {
        "query": "A dishwasher supply line leaked and damaged the kitchen floor",
        "expected_ids": [],
    },
    {
        "query": "Water pooled in the basement after several hours of heavy rain",
        "expected_ids": [1],
    },
    {
        "query": "My unattended car was struck on the rear quarter panel in a store parking lot",
        "expected_ids": [3],
    },
    {
        "query": "A pipe under the sink was tightened during a plumbing inspection before any leak occurred",
        "expected_ids": [],
    },
    {
        "query": "Rain came through the attic and damaged the ceiling, but the basement was unaffected",
        "expected_ids": [],
    },
    {
        "query": "Someone broke into my parked car and stole a bag from the back seat",
        "expected_ids": [],
    },
    {
        "query": "The cabinet beneath the sink was wet and warped after a plumbing leak",
        "expected_ids": [4],
    },
    {
        "query": "The lower level flooded when storm runoff entered through a basement window",
        "expected_ids": [1, 2],
    },
    {
        "query": "I noticed a dent on the rear bumper after leaving the car parked overnight",
        "expected_ids": [3],
    },
    {
        "query": "The basement was checked after the storm and everything was dry",
        "expected_ids": [],
    },
    {
        "query": "A plumber replaced the kitchen drain as part of a scheduled remodel",
        "expected_ids": [],
    },
    {
        "query": "A tree limb damaged the hood of the car while it was parked",
        "expected_ids": [],
    },
    {
        "query": "A sudden leak from plumbing below the kitchen sink soaked the cabinet base",
        "expected_ids": [4],
    },
    {
        "query": "Stormwater entered the cellar and soaked stored boxes",
        "expected_ids": [2],
    },
    {
        "query": "Another driver backed into my parked car and damaged the rear bumper",
        "expected_ids": [3],
    },
]

THRESHOLDS = [0.55]


def choose_best_claim(query: str, rows) -> int | None:
    candidate_lines = []

    for claim_id, claim_text, similarity in rows:
        candidate_lines.append(
            f"{claim_id}: {claim_text} (similarity: {similarity:.4f})"
        )

    candidates = "\n".join(candidate_lines)

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You are selecting the best historical insurance claim match "
                    "for a new claim. Compare all candidates together. "
                    "Choose the candidate representing the most similar actual loss event. "
                    "A match should have the same general cause and substantially similar "
                    "type of loss or damaged property. "
                    "Do not choose a candidate merely because it shares words, locations, "
                    "or broad subject matter. "
                    "Reject routine maintenance, preventive work, inspections with no loss, "
                    "explicit no-damage situations, different damage mechanisms, or materially "
                    "different loss events. "
                    "If the new claim explicitly says a particular area or property component "
                    "was not damaged, do not match it to a historical claim where that area "
                    "or component was damaged. "
                    "If none is a good match, answer NONE. "
                    "Otherwise answer only the numeric candidate ID."
                ),
            },
            {
                "role": "user",
                "content": f"""
NEW CLAIM:
{query}

CANDIDATES:
{candidates}

Choose the best candidate ID, or NONE.
""",
            },
        ],
    )

    answer = response.output_text.strip().upper()

    if answer == "NONE":
        return None

    try:
        return int(answer)
    except ValueError:
        return None


connection = psycopg.connect(
    host="localhost",
    port=5432,
    dbname="ai_intake",
    user="aiuser",
    password="aipassword",
)

register_vector(connection)


for threshold in THRESHOLDS:
    print()
    print(f"THRESHOLD: {threshold:.2f}")
    print("-" * 60)

    true_positives = 0
    true_negatives = 0
    false_positives = 0
    false_negatives = 0
    wrong_matches = 0

    for test in HOLDOUT_CASES:
        query = test["query"]
        expected_ids = test["expected_ids"]

        query_embedding = create_embedding(query)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    claim_text,
                    1 - (embedding <=> %s::vector) AS similarity
                FROM claim_embeddings
                WHERE 1 - (embedding <=> %s::vector) >= %s
                ORDER BY embedding <=> %s::vector
                LIMIT 3
                """,
                (
                    query_embedding,
                    query_embedding,
                    threshold,
                    query_embedding,
                ),
            )

            rows = cursor.fetchall()

        if rows:
            print()
            print("Top candidate matches:")

            for row in rows:
                print(row)

        actual_id = None
        matched_claim_text = None
        matched_similarity = None

        if rows:
            actual_id = choose_best_claim(query, rows)

            if actual_id is not None:
                for claim_id, claim_text, similarity in rows:
                    if claim_id == actual_id:
                        matched_claim_text = claim_text
                        matched_similarity = similarity
                        break

        if not expected_ids and actual_id is None:
            result_type = "TRUE NEGATIVE"
            true_negatives += 1

        elif not expected_ids and actual_id is not None:
            result_type = "FALSE POSITIVE"
            false_positives += 1

        elif expected_ids and actual_id is None:
            result_type = "FALSE NEGATIVE"
            false_negatives += 1

        elif actual_id in expected_ids:
            result_type = "TRUE POSITIVE"
            true_positives += 1

        else:
            result_type = "WRONG MATCH"
            wrong_matches += 1


        print()
        print(f"{result_type}: {query}")
        print(f"expected_ids: {expected_ids}")
        print(f"Actual:   {actual_id}")

        if matched_claim_text is not None:
            print(f"Matched claim text: {matched_claim_text}")
            print(f"Matched similarity: {matched_similarity:.4f}")

    correct = true_positives + true_negatives
    total = len(HOLDOUT_CASES)

    print()
    print("SUMMARY")
    print("-" * 60)
    print(f"True positives:  {true_positives}")
    print(f"True negatives:  {true_negatives}")
    print(f"False positives: {false_positives}")
    print(f"False negatives: {false_negatives}")
    print(f"Wrong matches:   {wrong_matches}")
    print(f"Accuracy:        {correct}/{total}")


connection.close()