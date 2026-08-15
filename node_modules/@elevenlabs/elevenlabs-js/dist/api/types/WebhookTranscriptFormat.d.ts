export declare const WebhookTranscriptFormat: {
    readonly Json: "json";
    readonly Opentelemetry: "opentelemetry";
};
export type WebhookTranscriptFormat = (typeof WebhookTranscriptFormat)[keyof typeof WebhookTranscriptFormat];
