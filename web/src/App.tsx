import type { IntakeResult } from "./types/IntakeResults";
import { createIntake } from "./services/intakeApi";
import IntakeForm from "./components/IntakeForm";
import { useState } from "react";

import "./App.css";

function App() {
  const [intakeText, setIntakeText] = useState("");
  const [result, setResult] = useState<IntakeResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit() {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await createIntake(intakeText);
      setResult(data);
    } catch (caughtError) {
      const message =
        caughtError instanceof Error
          ? caughtError.message
          : "An unexpected error occurred.";

      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main>
      <h1>AI Intake Validator</h1>

      <IntakeForm
        intakeText={intakeText}
        isLoading={isLoading}
        onTextChange={setIntakeText}
        onAnalyze={handleSubmit}
      />

      {error && (
        <section>
          <h2>Error</h2>
          <p>{error}</p>
        </section>
      )}

      {result && (
        <section>
          <h2>Analysis Result</h2>

          <dl>
            <dt>Claim type</dt>
            <dd>{result.claim_type}</dd>

            <dt>Severity</dt>
            <dd>{result.severity}</dd>

            <dt>Policy number</dt>
            <dd>{result.policy_number ?? "Not provided"}</dd>

            <dt>Date of loss</dt>
            <dd>{result.date_of_loss ?? "Not provided"}</dd>

            <dt>Description</dt>
            <dd>{result.description ?? "Not provided"}</dd>

            <dt>Potential preexisting issue</dt>
            <dd>{result.potential_preexisting_issue ? "Yes" : "No"}</dd>

            <dt>Missing fields</dt>
            <dd>
              {result.missing_fields.length > 0
                ? result.missing_fields.join(", ")
                : "None"}
            </dd>

            <dt>Requires review</dt>
            <dd>{result.requires_review ? "Yes" : "No"}</dd>

            <dt>Confidence</dt>
            <dd>{Math.round(result.confidence * 100)}%</dd>
          </dl>
        </section>
      )}
    </main>
  );
}

export default App;