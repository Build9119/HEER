import type * as ElevenLabs from "../index";
export interface GetConvAiSettingsResponseModel {
    conversationInitiationClientDataWebhook?: ElevenLabs.ConversationInitiationClientDataWebhook;
    webhooks?: ElevenLabs.ConvAiWebhooks;
    /** Whether the workspace can use MCP servers */
    canUseMcpServers?: boolean;
    ragRetentionPeriodDays?: number;
    /** Days to retain conversation embeddings. None means use the system default (30 days). */
    conversationEmbeddingRetentionDays?: number;
    defaultLivekitStack?: ElevenLabs.LivekitStackType;
}
