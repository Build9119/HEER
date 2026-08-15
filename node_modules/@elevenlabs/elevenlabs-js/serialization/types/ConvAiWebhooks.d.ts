import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { WebhookEventType } from "./WebhookEventType";
import { WebhookTranscriptFormat } from "./WebhookTranscriptFormat";
export declare const ConvAiWebhooks: core.serialization.ObjectSchema<serializers.ConvAiWebhooks.Raw, ElevenLabs.ConvAiWebhooks>;
export declare namespace ConvAiWebhooks {
    interface Raw {
        post_call_webhook_id?: string | null;
        events?: WebhookEventType.Raw[] | null;
        transcript_format?: WebhookTranscriptFormat.Raw | null;
        send_audio?: boolean | null;
    }
}
