import type * as ElevenLabs from "../index";
export interface ModerationGuardrailInput {
    executionMode?: ElevenLabs.GuardrailExecutionMode;
    config?: ElevenLabs.ModerationConfig;
}
