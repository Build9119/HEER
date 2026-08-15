import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ConversationHistoryTranscriptToolCallWebhookDetails } from "./ConversationHistoryTranscriptToolCallWebhookDetails";
export declare const ConversationHistoryTranscriptToolCallApiIntegrationWebhookDetailsInput: core.serialization.ObjectSchema<serializers.ConversationHistoryTranscriptToolCallApiIntegrationWebhookDetailsInput.Raw, ElevenLabs.ConversationHistoryTranscriptToolCallApiIntegrationWebhookDetailsInput>;
export declare namespace ConversationHistoryTranscriptToolCallApiIntegrationWebhookDetailsInput {
    interface Raw {
        integration_id?: string | null;
        credential_id?: string | null;
        integration_connection_id?: string | null;
        webhook_details: ConversationHistoryTranscriptToolCallWebhookDetails.Raw;
    }
}
