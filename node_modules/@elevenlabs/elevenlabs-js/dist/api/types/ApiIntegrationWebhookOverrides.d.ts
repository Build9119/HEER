import type * as ElevenLabs from "../index";
/**
 * A whitelist of fields that can be overridden by users when
 * configuring an API Integration Webhook Tool.
 */
export interface ApiIntegrationWebhookOverrides {
    schemaOverrides?: Record<string, ElevenLabs.ApiIntegrationWebhookOverridesSchemaOverridesValue | undefined>;
    requestHeaders?: Record<string, ElevenLabs.ApiIntegrationWebhookOverridesRequestHeadersValue | undefined>;
    responseFilterMode?: ElevenLabs.ResponseFilterMode;
    responseFilters?: string[];
}
