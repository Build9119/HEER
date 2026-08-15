import type * as ElevenLabs from "../index";
/**
 * Container for custom guardrails, matching ModerationGuardrail pattern
 */
export interface CustomGuardrailInput {
    config?: ElevenLabs.CustomGuardrailsConfigInput;
}
