import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const WebhookTranscriptFormat: core.serialization.Schema<serializers.WebhookTranscriptFormat.Raw, ElevenLabs.WebhookTranscriptFormat>;
export declare namespace WebhookTranscriptFormat {
    type Raw = "json" | "opentelemetry";
}
