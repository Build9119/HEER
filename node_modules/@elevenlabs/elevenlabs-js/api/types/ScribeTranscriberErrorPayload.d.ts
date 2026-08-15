/**
 * Payload for transcriber errors.
 */
export interface ScribeTranscriberErrorPayload {
    /** The message type identifier. */
    messageType: "transcriber_error";
    /** Transcriber error details. */
    error: string;
}
