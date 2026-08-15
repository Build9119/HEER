import type * as ElevenLabs from "../index";
export interface ConversationTurnMetrics {
    metrics?: Record<string, ElevenLabs.MetricRecord>;
    convaiAsrProvider?: string;
    convaiTtsModel?: string;
    convaiTtsCascade?: string;
}
