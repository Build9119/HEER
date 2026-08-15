import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { Llm } from "./Llm";
import { LlmDeprecationInfoModel } from "./LlmDeprecationInfoModel";
import { LlmReasoningEffort } from "./LlmReasoningEffort";
import { RegionalProcessingSurchargeInfo } from "./RegionalProcessingSurchargeInfo";
export declare const LlmInfoModelOutput: core.serialization.ObjectSchema<serializers.LlmInfoModelOutput.Raw, ElevenLabs.LlmInfoModelOutput>;
export declare namespace LlmInfoModelOutput {
    interface Raw {
        llm: Llm.Raw;
        is_checkpoint: boolean;
        max_tokens_limit: number;
        max_context_limit: number;
        supports_image_input: boolean;
        supports_document_input: boolean;
        supports_parallel_tool_calls: boolean;
        available_reasoning_efforts?: LlmReasoningEffort.Raw[] | null;
        deprecation_info?: LlmDeprecationInfoModel.Raw | null;
        regional_processing_surcharge?: RegionalProcessingSurchargeInfo.Raw | null;
    }
}
