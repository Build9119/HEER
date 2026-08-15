import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const PendingClipTaskType: core.serialization.Schema<serializers.PendingClipTaskType.Raw, ElevenLabs.PendingClipTaskType>;
export declare namespace PendingClipTaskType {
    type Raw = "preprocessing" | "speech_import" | "dubbing" | "video_to_music" | "media_generation";
}
