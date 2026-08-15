import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ConversationHistoryTranscriptToolCallWebhookDetails } from "./ConversationHistoryTranscriptToolCallWebhookDetails";
export declare const ConversationHistoryTranscriptToolCallApiIntegrationWebhookDetailsOutput: core.serialization.ObjectSchema<serializers.ConversationHistoryTranscriptToolCallApiIntegrationWebhookDetailsOutput.Raw, ElevenLabs.ConversationHistoryTranscriptToolCallApiIntegrationWebhookDetailsOutput>;
export declare namespace ConversationHistoryTranscriptToolCallApiIntegrationWebhookDetailsOutput {
    interface Raw {
        integration_id: string;
        credential_id: string;
        integration_connection_id: string;
        webhook_details: ConversationHistoryTranscriptToolCallWebhookDetails.Raw;
    }
}
