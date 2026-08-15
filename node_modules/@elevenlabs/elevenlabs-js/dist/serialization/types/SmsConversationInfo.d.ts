import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { SmsConversationInfoDirection } from "./SmsConversationInfoDirection";
export declare const SmsConversationInfo: core.serialization.ObjectSchema<serializers.SmsConversationInfo.Raw, ElevenLabs.SmsConversationInfo>;
export declare namespace SmsConversationInfo {
    interface Raw {
        direction: SmsConversationInfoDirection.Raw;
        phone_number_id?: string | null;
        sms_user_phone_number: string;
        agent_phone_number?: string | null;
    }
}
