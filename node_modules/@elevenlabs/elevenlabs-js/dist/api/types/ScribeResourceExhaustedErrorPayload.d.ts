/**
 * Payload for resource exhausted errors.
 */
export interface ScribeResourceExhaustedErrorPayload {
    /** The message type identifier. */
    messageType: "resource_exhausted";
    /** Resource exhausted error details. */
    error: string;
}
