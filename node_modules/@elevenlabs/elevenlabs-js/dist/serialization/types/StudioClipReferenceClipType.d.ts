import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const StudioClipReferenceClipType: core.serialization.Schema<serializers.StudioClipReferenceClipType.Raw, ElevenLabs.StudioClipReferenceClipType>;
export declare namespace StudioClipReferenceClipType {
    type Raw = "video" | "image" | "external_audio" | "tts_node";
}
