import type * as ElevenLabs from "../index";
export interface ContentGuardrailInput {
    executionMode?: ElevenLabs.GuardrailExecutionMode;
    config?: ElevenLabs.ContentConfig;
    triggerAction?: ElevenLabs.ContentGuardrailInputTriggerAction;
}
