/**
 * Payload for input errors.
 */
export interface ScribeInputErrorPayload {
    /** The message type identifier. */
    messageType: "input_error";
    /** Input error details. */
    error: string;
}
