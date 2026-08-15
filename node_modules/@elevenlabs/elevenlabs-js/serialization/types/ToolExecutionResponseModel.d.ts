import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ToolExecutionResponseModelToolCallDetails } from "./ToolExecutionResponseModelToolCallDetails";
export declare const ToolExecutionResponseModel: core.serialization.ObjectSchema<serializers.ToolExecutionResponseModel.Raw, ElevenLabs.ToolExecutionResponseModel>;
export declare namespace ToolExecutionResponseModel {
    interface Raw {
        tool_id: string;
        tool_request_id: string;
        conversation_id: string;
        agent_id: string;
        branch_id?: string | null;
        timestamp: number;
        latency_secs: number;
        is_error?: boolean | null;
        request_payload?: string | null;
        response_payload?: string | null;
        error_message?: string | null;
        error_type?: string | null;
        id: string;
        tool_call_details?: ToolExecutionResponseModelToolCallDetails.Raw | null;
    }
}
