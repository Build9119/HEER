import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { BatchCallStatus } from "./BatchCallStatus";
import { BatchCallWhatsAppParams } from "./BatchCallWhatsAppParams";
import { OutboundCallRecipientResponseModel } from "./OutboundCallRecipientResponseModel";
import { TelephonyCallConfig } from "./TelephonyCallConfig";
import { TelephonyProvider } from "./TelephonyProvider";
export declare const BatchCallDetailedResponse: core.serialization.ObjectSchema<serializers.BatchCallDetailedResponse.Raw, ElevenLabs.BatchCallDetailedResponse>;
export declare namespace BatchCallDetailedResponse {
    interface Raw {
        id: string;
        phone_number_id?: string | null;
        phone_provider?: TelephonyProvider.Raw | null;
        whatsapp_params?: BatchCallWhatsAppParams.Raw | null;
        name: string;
        agent_id: string;
        branch_id?: string | null;
        environment?: string | null;
        created_at_unix: number;
        scheduled_time_unix: number;
        timezone?: string | null;
        total_calls_dispatched: number;
        total_calls_scheduled: number;
        total_calls_finished: number;
        last_updated_at_unix: number;
        status: BatchCallStatus.Raw;
        retry_count: number;
        telephony_call_config: TelephonyCallConfig.Raw;
        target_concurrency_limit?: number | null;
        agent_name: string;
        branch_name?: string | null;
        recipients: OutboundCallRecipientResponseModel.Raw[];
    }
}
