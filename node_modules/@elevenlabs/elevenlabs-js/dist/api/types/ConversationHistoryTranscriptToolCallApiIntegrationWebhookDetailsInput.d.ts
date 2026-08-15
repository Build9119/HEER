import type * as ElevenLabs from "../index";
export interface ConversationHistoryTranscriptToolCallApiIntegrationWebhookDetailsInput {
    integrationId?: string;
    credentialId?: string;
    integrationConnectionId?: string;
    webhookDetails: ElevenLabs.ConversationHistoryTranscriptToolCallWebhookDetails;
}
