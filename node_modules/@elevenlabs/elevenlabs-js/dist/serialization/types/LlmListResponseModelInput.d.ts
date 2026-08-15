import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { LlmDeprecationConfigModel } from "./LlmDeprecationConfigModel";
import { LlmInfoModelInput } from "./LlmInfoModelInput";
export declare const LlmListResponseModelInput: core.serialization.ObjectSchema<serializers.LlmListResponseModelInput.Raw, ElevenLabs.LlmListResponseModelInput>;
export declare namespace LlmListResponseModelInput {
    interface Raw {
        llms: LlmInfoModelInput.Raw[];
        default_deprecation_config: LlmDeprecationConfigModel.Raw;
    }
}
