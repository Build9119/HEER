import type * as ElevenLabs from "../index";
export interface AudioAnalysis {
    status: ElevenLabs.AudioAnalysisStatus;
    data?: ElevenLabs.AudioAnalysisResult;
    updatedAtMs?: number;
}
