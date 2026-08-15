import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ApiIntegrationWebhookOverridesRequestHeadersValue } from "./ApiIntegrationWebhookOverridesRequestHeadersValue";
import { ApiIntegrationWebhookOverridesSchemaOverridesValue } from "./ApiIntegrationWebhookOverridesSchemaOverridesValue";
import { ResponseFilterMode } from "./ResponseFilterMode";
export declare const ApiIntegrationWebhookOverrides: core.serialization.ObjectSchema<serializers.ApiIntegrationWebhookOverrides.Raw, ElevenLabs.ApiIntegrationWebhookOverrides>;
export declare namespace ApiIntegrationWebhookOverrides {
    interface Raw {
        schema_overrides?: Record<string, ApiIntegrationWebhookOverridesSchemaOverridesValue.Raw | null | undefined> | null;
        request_headers?: Record<string, ApiIntegrationWebhookOverridesRequestHeadersValue.Raw | null | undefined> | null;
        response_filter_mode?: ResponseFilterMode.Raw | null;
        response_filters?: string[] | null;
    }
}
