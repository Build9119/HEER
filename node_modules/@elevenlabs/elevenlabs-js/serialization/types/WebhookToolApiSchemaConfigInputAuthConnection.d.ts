import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { AuthConnectionLocator } from "./AuthConnectionLocator";
import { EnvironmentAuthConnectionLocator } from "./EnvironmentAuthConnectionLocator";
export declare const WebhookToolApiSchemaConfigInputAuthConnection: core.serialization.Schema<serializers.WebhookToolApiSchemaConfigInputAuthConnection.Raw, ElevenLabs.WebhookToolApiSchemaConfigInputAuthConnection>;
export declare namespace WebhookToolApiSchemaConfigInputAuthConnection {
    type Raw = AuthConnectionLocator.Raw | EnvironmentAuthConnectionLocator.Raw;
}
