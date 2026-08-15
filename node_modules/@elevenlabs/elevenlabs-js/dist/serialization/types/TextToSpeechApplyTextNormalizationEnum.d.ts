import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const TextToSpeechApplyTextNormalizationEnum: core.serialization.Schema<serializers.TextToSpeechApplyTextNormalizationEnum.Raw, ElevenLabs.TextToSpeechApplyTextNormalizationEnum>;
export declare namespace TextToSpeechApplyTextNormalizationEnum {
    type Raw = "auto" | "on" | "off";
}
