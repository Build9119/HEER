import type * as ElevenLabs from "../index";
export interface ModerationGuardrailOutput {
    executionMode?: ElevenLabs.GuardrailExecutionMode;
    config?: ElevenLabs.ModerationConfig;
}
