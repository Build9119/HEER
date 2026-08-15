import type * as ElevenLabs from "../index";
export interface ContentGuardrailOutput {
    executionMode?: ElevenLabs.GuardrailExecutionMode;
    config?: ElevenLabs.ContentConfig;
    triggerAction?: ElevenLabs.ContentGuardrailOutputTriggerAction;
}
