import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const VideoAnalysisStatus: core.serialization.Schema<serializers.VideoAnalysisStatus.Raw, ElevenLabs.VideoAnalysisStatus>;
export declare namespace VideoAnalysisStatus {
    type Raw = "processing" | "completed" | "failed";
}
