import type * as ElevenLabs from "../index";
export type ToolExecutionResponseModelToolCallDetails = ElevenLabs.ToolExecutionResponseModelToolCallDetails.ApiIntegrationWebhook | ElevenLabs.ToolExecutionResponseModelToolCallDetails.Client | ElevenLabs.ToolExecutionResponseModelToolCallDetails.Mcp | ElevenLabs.ToolExecutionResponseModelToolCallDetails.Webhook;
export declare namespace ToolExecutionResponseModelToolCallDetails {
    interface ApiIntegrationWebhook extends ElevenLabs.ConversationHistoryTranscriptToolCallApiIntegrationWebhookDetailsOutput {
        type: "api_integration_webhook";
    }
    interface Client extends ElevenLabs.ConversationHistoryTranscriptToolCallClientDetails {
        type: "client";
    }
    interface Mcp extends ElevenLabs.ConversationHistoryTranscriptToolCallMcpDetails {
        type: "mcp";
    }
    interface Webhook extends ElevenLabs.ConversationHistoryTranscriptToolCallWebhookDetails {
        type: "webhook";
    }
}
