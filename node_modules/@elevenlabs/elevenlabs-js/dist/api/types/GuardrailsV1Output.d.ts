import type * as ElevenLabs from "../index";
export interface GuardrailsV1Output {
    version?: "1";
    focus?: ElevenLabs.FocusGuardrail;
    promptInjection?: ElevenLabs.PromptInjectionGuardrail;
    content?: ElevenLabs.ContentGuardrailOutput;
    custom?: ElevenLabs.CustomGuardrailOutput;
}
