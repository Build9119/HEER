import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { VideoAnalysisResult } from "./VideoAnalysisResult";
import { VideoAnalysisStatus } from "./VideoAnalysisStatus";
export declare const VideoAnalysis: core.serialization.ObjectSchema<serializers.VideoAnalysis.Raw, ElevenLabs.VideoAnalysis>;
export declare namespace VideoAnalysis {
    interface Raw {
        status: VideoAnalysisStatus.Raw;
        data?: VideoAnalysisResult.Raw | null;
        updated_at_ms?: number | null;
    }
}
