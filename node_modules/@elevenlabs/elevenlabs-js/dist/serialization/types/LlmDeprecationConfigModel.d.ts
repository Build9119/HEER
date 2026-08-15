import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const LlmDeprecationConfigModel: core.serialization.ObjectSchema<serializers.LlmDeprecationConfigModel.Raw, ElevenLabs.LlmDeprecationConfigModel>;
export declare namespace LlmDeprecationConfigModel {
    interface Raw {
        warning_start_days: number;
        fallback_start_days: number;
        fallback_complete_days: number;
        fallback_start_percentage: number;
        fallback_complete_percentage: number;
    }
}
