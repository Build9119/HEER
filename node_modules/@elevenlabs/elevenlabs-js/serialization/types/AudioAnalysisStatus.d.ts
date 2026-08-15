import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const AudioAnalysisStatus: core.serialization.Schema<serializers.AudioAnalysisStatus.Raw, ElevenLabs.AudioAnalysisStatus>;
export declare namespace AudioAnalysisStatus {
    type Raw = "processing" | "completed" | "failed";
}
