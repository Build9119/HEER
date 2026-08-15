import type * as ElevenLabs from "../index";
export interface ContentConfig {
    sexual?: ElevenLabs.ContentThresholdGuardrail;
    violence?: ElevenLabs.ContentThresholdGuardrail;
    harassment?: ElevenLabs.ContentThresholdGuardrail;
    selfHarm?: ElevenLabs.ContentThresholdGuardrail;
    profanity?: ElevenLabs.ContentThresholdGuardrail;
    religionOrPolitics?: ElevenLabs.ContentThresholdGuardrail;
    medicalAndLegalInformation?: ElevenLabs.ContentThresholdGuardrail;
}
