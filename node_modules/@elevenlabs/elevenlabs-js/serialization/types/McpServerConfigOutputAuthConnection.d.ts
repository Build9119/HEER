import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { AuthConnectionLocator } from "./AuthConnectionLocator";
import { EnvironmentAuthConnectionLocator } from "./EnvironmentAuthConnectionLocator";
export declare const McpServerConfigOutputAuthConnection: core.serialization.Schema<serializers.McpServerConfigOutputAuthConnection.Raw, ElevenLabs.McpServerConfigOutputAuthConnection>;
export declare namespace McpServerConfigOutputAuthConnection {
    type Raw = AuthConnectionLocator.Raw | EnvironmentAuthConnectionLocator.Raw;
}
