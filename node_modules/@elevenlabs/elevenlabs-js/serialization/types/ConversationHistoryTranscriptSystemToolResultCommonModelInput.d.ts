import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ConversationHistoryTranscriptSystemToolResultCommonModelInputResult } from "./ConversationHistoryTranscriptSystemToolResultCommonModelInputResult";
import { DynamicVariableUpdateCommonModel } from "./DynamicVariableUpdateCommonModel";
export declare const ConversationHistoryTranscriptSystemToolResultCommonModelInput: core.serialization.ObjectSchema<serializers.ConversationHistoryTranscriptSystemToolResultCommonModelInput.Raw, ElevenLabs.ConversationHistoryTranscriptSystemToolResultCommonModelInput>;
export declare namespace ConversationHistoryTranscriptSystemToolResultCommonModelInput {
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
        result?: ConversationHistoryTranscriptSystemToolResultCommonModelInputResult.Raw | null;
    }
}
