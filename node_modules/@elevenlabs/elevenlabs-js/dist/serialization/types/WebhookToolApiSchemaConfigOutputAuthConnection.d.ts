import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { AuthConnectionLocator } from "./AuthConnectionLocator";
import { EnvironmentAuthConnectionLocator } from "./EnvironmentAuthConnectionLocator";
export declare const WebhookToolApiSchemaConfigOutputAuthConnection: core.serialization.Schema<serializers.WebhookToolApiSchemaConfigOutputAuthConnection.Raw, ElevenLabs.WebhookToolApiSchemaConfigOutputAuthConnection>;
export declare namespace WebhookToolApiSchemaConfigOutputAuthConnection {
    type Raw = AuthConnectionLocator.Raw | EnvironmentAuthConnectionLocator.Raw;
}
