/**
 * Payload for session time limit exceeded errors.
 */
export interface ScribeSessionTimeLimitExceededErrorPayload {
    /** The message type identifier. */
    messageType: "session_time_limit_exceeded";
    /** Session time limit exceeded error details. */
    error: string;
}
