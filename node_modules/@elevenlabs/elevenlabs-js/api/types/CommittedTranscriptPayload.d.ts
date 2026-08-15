/**
 * Payload for committed transcription results.
 */
export interface CommittedTranscriptPayload {
    /** The message type identifier. */
    messageType: "committed_transcript";
    /** Committed transcription text. */
    text: string;
}
