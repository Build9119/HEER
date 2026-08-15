import type * as ElevenLabs from "../index";
export interface SmsConversationInfo {
    direction: ElevenLabs.SmsConversationInfoDirection;
    phoneNumberId?: string;
    smsUserPhoneNumber: string;
    agentPhoneNumber?: string;
}
