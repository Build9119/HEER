/**
 * Payload for rate limited errors.
 */
export interface ScribeRateLimitedErrorPayload {
    /** The message type identifier. */
    messageType: "rate_limited";
    /** Rate limited error details. */
    error: string;
}
