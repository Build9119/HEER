import type * as ElevenLabs from "../index";
export interface VideoAnalysis {
    status: ElevenLabs.VideoAnalysisStatus;
    data?: ElevenLabs.VideoAnalysisResult;
    updatedAtMs?: number;
}
