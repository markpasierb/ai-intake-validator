export type IntakeResult = {
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
