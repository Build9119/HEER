import type * as ElevenLabs from "../index";
export interface AstllmNodeInputValueSchema {
    type?: "llm";
    /** JSON schema describing the value that the LLM should extract. */
    valueSchema: ElevenLabs.LlmLiteralJsonSchemaProperty;
}
