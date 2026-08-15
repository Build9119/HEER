import type * as ElevenLabs from "../../../../../../../api/index";
import * as core from "../../../../../../../core";
import type * as serializers from "../../../../../../index";
import { BatchCallWhatsAppParams } from "../../../../../../types/BatchCallWhatsAppParams";
import { OutboundCallRecipient } from "../../../../../../types/OutboundCallRecipient";
import { TelephonyCallConfig } from "../../../../../../types/TelephonyCallConfig";
export declare const BodySubmitABatchCallRequestV1ConvaiBatchCallingSubmitPost: core.serialization.Schema<serializers.conversationalAi.BodySubmitABatchCallRequestV1ConvaiBatchCallingSubmitPost.Raw, ElevenLabs.conversationalAi.BodySubmitABatchCallRequestV1ConvaiBatchCallingSubmitPost>;
export declare namespace BodySubmitABatchCallRequestV1ConvaiBatchCallingSubmitPost {
    interface Raw {
        call_name: string;
        agent_id: string;
        recipients: OutboundCallRecipient.Raw[];
        scheduled_time_unix?: number | null;
        agent_phone_number_id?: string | null;
        whatsapp_params?: BatchCallWhatsAppParams.Raw | null;
        timezone?: string | null;
        branch_id?: string | null;
        environment?: string | null;
        telephony_call_config?: TelephonyCallConfig.Raw | null;
        target_concurrency_limit?: number | null;
    }
}
