export interface SayNodePromptMessageOutput {
    type: "prompt";
    /** LLM prompt describing what message should be generated. */
    prompt: string;
}
