/**
 * Payload for unaccepted terms errors.
 */
export interface ScribeUnacceptedTermsErrorPayload {
    /** The message type identifier. */
    messageType: "unaccepted_terms";
    /** Unaccepted terms error details. */
    error: string;
}
