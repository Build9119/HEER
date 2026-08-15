import type * as ElevenLabs from "../index";
export interface ConversationHistorySipTrunkingPhoneCallModel {
    direction: ElevenLabs.TelephonyDirection;
    phoneNumberId: string;
    agentNumber: string;
    externalNumber: string;
    callId?: string;
    callSid: string;
    sipHeaderDynamicVariables?: Record<string, string>;
}
