type IntakeFormProps = {
    intakeText: string;
    isLoading: boolean;
    onTextChange: (text: string) => void;
    onAnalyze: () => void;
};

function IntakeForm({
    intakeText,
    isLoading,
    onTextChange,
    onAnalyze,
}: IntakeFormProps) {
    return (
        <>
            <label htmlFor="intake-text">
                Intake narrative
            </label>

            <textarea
                id="intake-text"
                value={intakeText}
                onChange={(event) =>
                    onTextChange(event.target.value)
                }
                rows={12}
                placeholder="Enter an insurance intake narrative..."
            />

            <button
                type="button"
                onClick={onAnalyze}
                disabled={!intakeText.trim() || isLoading}
            >
                {isLoading
                    ? "Analyzing..."
                    : "Analyze Intake"}
            </button>
        </>
    );
}

export default IntakeForm;