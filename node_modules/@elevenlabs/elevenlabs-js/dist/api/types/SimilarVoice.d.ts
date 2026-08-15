import type * as ElevenLabs from "../index";
export interface SimilarVoice {
    voiceId: string;
    name: string;
    category: ElevenLabs.VoiceCategory;
    description?: string;
    previewUrl?: string;
}
