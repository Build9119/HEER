import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { LlmDeprecationConfigModel } from "./LlmDeprecationConfigModel";
import { LlmInfoModelOutput } from "./LlmInfoModelOutput";
export declare const LlmListResponseModelOutput: core.serialization.ObjectSchema<serializers.LlmListResponseModelOutput.Raw, ElevenLabs.LlmListResponseModelOutput>;
export declare namespace LlmListResponseModelOutput {
    interface Raw {
        llms: LlmInfoModelOutput.Raw[];
        default_deprecation_config: LlmDeprecationConfigModel.Raw;
    }
}
