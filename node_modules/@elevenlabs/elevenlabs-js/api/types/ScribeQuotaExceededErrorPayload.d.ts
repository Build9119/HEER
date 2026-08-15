/**
 * Payload for quota exceeded errors.
 */
export interface ScribeQuotaExceededErrorPayload {
    /** The message type identifier. */
    messageType: "quota_exceeded";
    /** Quota exceeded error details. */
    error: string;
}
