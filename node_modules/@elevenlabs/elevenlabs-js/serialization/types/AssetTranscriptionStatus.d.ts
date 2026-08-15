import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const AssetTranscriptionStatus: core.serialization.Schema<serializers.AssetTranscriptionStatus.Raw, ElevenLabs.AssetTranscriptionStatus>;
export declare namespace AssetTranscriptionStatus {
    type Raw = "processing" | "completed" | "failed";
}
