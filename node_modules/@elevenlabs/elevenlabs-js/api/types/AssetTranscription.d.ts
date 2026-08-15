import type * as ElevenLabs from "../index";
export interface AssetTranscription {
    status: ElevenLabs.AssetTranscriptionStatus;
    data?: ElevenLabs.AssetTranscriptionData;
    updatedAtMs?: number;
}
