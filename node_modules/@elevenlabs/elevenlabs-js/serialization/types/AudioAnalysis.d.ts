import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { AudioAnalysisResult } from "./AudioAnalysisResult";
import { AudioAnalysisStatus } from "./AudioAnalysisStatus";
export declare const AudioAnalysis: core.serialization.ObjectSchema<serializers.AudioAnalysis.Raw, ElevenLabs.AudioAnalysis>;
export declare namespace AudioAnalysis {
    interface Raw {
        status: AudioAnalysisStatus.Raw;
        data?: AudioAnalysisResult.Raw | null;
        updated_at_ms?: number | null;
    }
}
