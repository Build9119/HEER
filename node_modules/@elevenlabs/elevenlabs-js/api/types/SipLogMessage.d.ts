import type * as ElevenLabs from "../index";
export interface SipLogMessage {
    callId: string;
    phoneNumbers: string[];
    localAddress: string;
    remoteAddress: string;
    transport: string;
    rawMessage: string;
    errorMessage: string;
    direction: ElevenLabs.SipLogMessageDirection;
    createdAtUnixMicro: number;
}
