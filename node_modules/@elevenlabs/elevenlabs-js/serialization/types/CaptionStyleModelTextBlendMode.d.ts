import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CaptionStyleModelTextBlendMode: core.serialization.Schema<serializers.CaptionStyleModelTextBlendMode.Raw, ElevenLabs.CaptionStyleModelTextBlendMode>;
export declare namespace CaptionStyleModelTextBlendMode {
    type Raw = "normal" | "difference" | "multiply";
}
