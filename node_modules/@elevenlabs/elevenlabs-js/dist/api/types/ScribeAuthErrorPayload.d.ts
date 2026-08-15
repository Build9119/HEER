/**
 * Payload for authentication errors.
 */
export interface ScribeAuthErrorPayload {
    /** The message type identifier. */
    messageType: "auth_error";
    /** Authentication error details. */
    error: string;
}
