import type * as ElevenLabs from "../index";
export interface ImageAnalysis {
    status: ElevenLabs.ImageAnalysisStatus;
    data?: ElevenLabs.ImageAnalysisResult;
    updatedAtMs?: number;
}
