import type * as ElevenLabs from "../index";
export interface GetSipLogMessagesResponse {
    sipMessages: ElevenLabs.SipLogMessage[];
    nextCursor?: string;
    hasMore?: boolean;
}
