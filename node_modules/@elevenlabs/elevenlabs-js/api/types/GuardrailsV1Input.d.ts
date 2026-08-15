import type * as ElevenLabs from "../index";
export interface GuardrailsV1Input {
    version?: "1";
    focus?: ElevenLabs.FocusGuardrail;
    promptInjection?: ElevenLabs.PromptInjectionGuardrail;
    content?: ElevenLabs.ContentGuardrailInput;
    custom?: ElevenLabs.CustomGuardrailInput;
}
