import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { DynamicVariableUpdateCommonModel } from "./DynamicVariableUpdateCommonModel";
export declare const ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelOutput: core.serialization.ObjectSchema<serializers.ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelOutput.Raw, ElevenLabs.ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelOutput>;
export declare namespace ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelOutput {
    interface Raw {
        request_id: string;
        tool_name: string;
        result_value: string;
        is_error: boolean;
        is_blocked: boolean;
        tool_has_been_called: boolean;
        tool_latency_secs: number;
        error_type: string;
        raw_error_message: string;
        dynamic_variable_updates: DynamicVariableUpdateCommonModel.Raw[];
        type: "api_integration_webhook";
        integration_id: string;
        credential_id: string;
        integration_connection_id: string;
    }
}
