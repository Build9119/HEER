export interface SayNodePromptMessageInput {
    type?: "prompt";
    /** LLM prompt describing what message should be generated. */
    prompt: string;
}
