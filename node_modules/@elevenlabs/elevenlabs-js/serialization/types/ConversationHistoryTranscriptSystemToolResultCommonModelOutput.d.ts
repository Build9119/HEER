import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ConversationHistoryTranscriptSystemToolResultCommonModelOutputResult } from "./ConversationHistoryTranscriptSystemToolResultCommonModelOutputResult";
import { DynamicVariableUpdateCommonModel } from "./DynamicVariableUpdateCommonModel";
export declare const ConversationHistoryTranscriptSystemToolResultCommonModelOutput: core.serialization.ObjectSchema<serializers.ConversationHistoryTranscriptSystemToolResultCommonModelOutput.Raw, ElevenLabs.ConversationHistoryTranscriptSystemToolResultCommonModelOutput>;
export declare namespace ConversationHistoryTranscriptSystemToolResultCommonModelOutput {
    interface Raw {
        request_id: string;
        tool_name: string;
        result_value: string;
        is_error: boolean;
        is_blocked?: boolean | null;
        tool_has_been_called: boolean;
        tool_latency_secs?: number | null;
        error_type?: string | null;
        raw_error_message?: string | null;
        dynamic_variable_updates?: DynamicVariableUpdateCommonModel.Raw[] | null;
        type: "system";
        result?: ConversationHistoryTranscriptSystemToolResultCommonModelOutputResult.Raw | null;
    }
}
