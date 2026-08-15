import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { DynamicVariableUpdateCommonModel } from "./DynamicVariableUpdateCommonModel";
export declare const ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelInput: core.serialization.ObjectSchema<serializers.ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelInput.Raw, ElevenLabs.ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelInput>;
export declare namespace ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelInput {
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
        type: "api_integration_webhook";
        integration_id?: string | null;
        credential_id?: string | null;
        integration_connection_id?: string | null;
    }
}
