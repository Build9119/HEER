import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { Llm } from "./Llm";
import { LlmDeprecationConfigModel } from "./LlmDeprecationConfigModel";
export declare const LlmDeprecationInfoModel: core.serialization.ObjectSchema<serializers.LlmDeprecationInfoModel.Raw, ElevenLabs.LlmDeprecationInfoModel>;
export declare namespace LlmDeprecationInfoModel {
    interface Raw {
        llm: Llm.Raw;
        is_deprecated: boolean;
        is_in_warning_period?: boolean | null;
        is_in_fallback_period?: boolean | null;
        fallback_percentage?: number | null;
        provider_deprecation_date?: string | null;
        replacement_model?: Llm.Raw | null;
        deprecation_config?: LlmDeprecationConfigModel.Raw | null;
    }
}
