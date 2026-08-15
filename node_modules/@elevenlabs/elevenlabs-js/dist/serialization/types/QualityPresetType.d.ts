import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const QualityPresetType: core.serialization.Schema<serializers.QualityPresetType.Raw, ElevenLabs.QualityPresetType>;
export declare namespace QualityPresetType {
    type Raw = "standard" | "high" | "ultra" | "ultra_lossless";
}
