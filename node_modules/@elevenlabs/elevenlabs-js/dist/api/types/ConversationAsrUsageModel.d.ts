/**
 * Aggregated ASR usage for a conversation (analytics-only, not billing).
 */
export interface ConversationAsrUsageModel {
    asrModel?: string;
    totalTranscriptionCalls?: number;
    totalAudioInputSeconds?: number;
}
