import type { IntakeResult } from "../types/IntakeResult";

const NODE_API_URL = "http://localhost:3000";

export async function createIntake(
  text: string,
): Promise<IntakeResult> {
  const response = await fetch(`${NODE_API_URL}/intake`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error(
      `Request failed: ${response.status} ${response.statusText}`,
    );
  }

  return (await response.json()) as IntakeResult;
}