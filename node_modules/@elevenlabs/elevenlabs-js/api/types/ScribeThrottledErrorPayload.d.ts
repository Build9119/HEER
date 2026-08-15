/**
 * Payload for throttled errors.
 */
export interface ScribeThrottledErrorPayload {
    /** The message type identifier. */
    messageType: "commit_throttled";
    /** Throttled error details. */
    error: string;
}
