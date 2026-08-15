/**
 * Payload for queue overflow errors.
 */
export interface ScribeQueueOverflowErrorPayload {
    /** The message type identifier. */
    messageType: "queue_overflow";
    /** Queue overflow error details. */
    error: string;
}
