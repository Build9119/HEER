/** Response format. Defaults to 'json'. Set to 'opentelemetry' for an OTLP-compatible trace payload using the same structure as the post-call webhook. */
export declare const ConversationsGetRequestFormat: {
    readonly Json: "json";
    readonly Opentelemetry: "opentelemetry";
};
export type ConversationsGetRequestFormat = (typeof ConversationsGetRequestFormat)[keyof typeof ConversationsGetRequestFormat];
