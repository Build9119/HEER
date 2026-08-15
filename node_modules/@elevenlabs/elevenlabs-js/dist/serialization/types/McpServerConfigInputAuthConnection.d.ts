import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { AuthConnectionLocator } from "./AuthConnectionLocator";
import { EnvironmentAuthConnectionLocator } from "./EnvironmentAuthConnectionLocator";
export declare const McpServerConfigInputAuthConnection: core.serialization.Schema<serializers.McpServerConfigInputAuthConnection.Raw, ElevenLabs.McpServerConfigInputAuthConnection>;
export declare namespace McpServerConfigInputAuthConnection {
    type Raw = AuthConnectionLocator.Raw | EnvironmentAuthConnectionLocator.Raw;
}
