import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { TelephonyDirection } from "./TelephonyDirection";
export declare const ConversationHistorySipTrunkingPhoneCallModel: core.serialization.ObjectSchema<serializers.ConversationHistorySipTrunkingPhoneCallModel.Raw, ElevenLabs.ConversationHistorySipTrunkingPhoneCallModel>;
export declare namespace ConversationHistorySipTrunkingPhoneCallModel {
    interface Raw {
        direction: TelephonyDirection.Raw;
        phone_number_id: string;
        agent_number: string;
        external_number: string;
        call_id?: string | null;
        call_sid: string;
        sip_header_dynamic_variables?: Record<string, string> | null;
    }
}
