import type { IntakeResult } from "./types/IntakeResults";
import AnalysisResult from "./components/AnalysisResult";
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

      {result && <AnalysisResult result={result} />}
    </main>
  );
}

export default App;