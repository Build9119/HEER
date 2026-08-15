import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ImageAnalysisStatus: core.serialization.Schema<serializers.ImageAnalysisStatus.Raw, ElevenLabs.ImageAnalysisStatus>;
export declare namespace ImageAnalysisStatus {
    type Raw = "processing" | "completed" | "failed";
}
