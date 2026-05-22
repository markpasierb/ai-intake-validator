type IntakeResult = {
  claim_type: string;
  severity: "low" | "medium" | "high";
  policy_number: string | null;
  date_of_loss: string | null;
  description: string | null;
  potential_preexisting_issue: boolean;
  missing_fields: string[];
  requires_review: boolean;
  confidence: number;
};

const API_BASE_URL = "http://127.0.0.1:8000";

async function createIntake(text: string): Promise<IntakeResult> {
  const response = await fetch(`${API_BASE_URL}/intake`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<IntakeResult>;
}

async function main() {
  const result = await createIntake(
    "Customer reports minor siding damage from wind on 2026-05-10. Cosmetic scratches only. Policy number POL-77821."
  );

  console.log(result);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});