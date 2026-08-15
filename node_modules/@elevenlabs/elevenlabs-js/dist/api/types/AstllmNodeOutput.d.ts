import type * as ElevenLabs from "../index";
export interface AstllmNodeOutput {
    /** JSON schema describing the value that the LLM should extract. */
    valueSchema: ElevenLabs.LlmLiteralJsonSchemaProperty;
    /** The prompt to evaluate to a boolean value. Deprecated. Use a boolean schema instead. */
    prompt: string;
}
