export interface AstllmNodeInputPrompt {
    type?: "llm";
    /** The prompt to evaluate to a boolean value. Deprecated. Use a boolean schema instead. */
    prompt: string;
}
