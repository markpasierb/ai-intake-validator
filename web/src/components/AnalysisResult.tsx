import type { IntakeResult } from "../types/IntakeResult";

type AnalysisResultProps = {
  result: IntakeResult;
};

function AnalysisResult({ result }: AnalysisResultProps) {
  return (
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
  );
}

export default AnalysisResult;