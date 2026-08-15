import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ConvAiDynamicVariable } from "./ConvAiDynamicVariable";
export declare const ApiIntegrationWebhookOverridesRequestHeadersValue: core.serialization.Schema<serializers.ApiIntegrationWebhookOverridesRequestHeadersValue.Raw, ElevenLabs.ApiIntegrationWebhookOverridesRequestHeadersValue>;
export declare namespace ApiIntegrationWebhookOverridesRequestHeadersValue {
    type Raw = string | ConvAiDynamicVariable.Raw;
}
