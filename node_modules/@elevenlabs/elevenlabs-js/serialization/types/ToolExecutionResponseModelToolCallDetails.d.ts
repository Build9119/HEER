import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ConversationHistoryTranscriptToolCallApiIntegrationWebhookDetailsOutput } from "./ConversationHistoryTranscriptToolCallApiIntegrationWebhookDetailsOutput";
import { ConversationHistoryTranscriptToolCallClientDetails } from "./ConversationHistoryTranscriptToolCallClientDetails";
import { ConversationHistoryTranscriptToolCallMcpDetails } from "./ConversationHistoryTranscriptToolCallMcpDetails";
import { ConversationHistoryTranscriptToolCallWebhookDetails } from "./ConversationHistoryTranscriptToolCallWebhookDetails";
export declare const ToolExecutionResponseModelToolCallDetails: core.serialization.Schema<serializers.ToolExecutionResponseModelToolCallDetails.Raw, ElevenLabs.ToolExecutionResponseModelToolCallDetails>;
export declare namespace ToolExecutionResponseModelToolCallDetails {
    type Raw = ToolExecutionResponseModelToolCallDetails.ApiIntegrationWebhook | ToolExecutionResponseModelToolCallDetails.Client | ToolExecutionResponseModelToolCallDetails.Mcp | ToolExecutionResponseModelToolCallDetails.Webhook;
    interface ApiIntegrationWebhook extends ConversationHistoryTranscriptToolCallApiIntegrationWebhookDetailsOutput.Raw {
        type: "api_integration_webhook";
    }
    interface Client extends ConversationHistoryTranscriptToolCallClientDetails.Raw {
        type: "client";
    }
    interface Mcp extends ConversationHistoryTranscriptToolCallMcpDetails.Raw {
        type: "mcp";
    }
    interface Webhook extends ConversationHistoryTranscriptToolCallWebhookDetails.Raw {
        type: "webhook";
    }
}
