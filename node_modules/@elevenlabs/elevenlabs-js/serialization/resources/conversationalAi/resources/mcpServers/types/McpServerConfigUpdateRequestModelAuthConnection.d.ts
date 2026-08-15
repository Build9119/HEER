import type * as ElevenLabs from "../../../../../../api/index";
import * as core from "../../../../../../core";
import type * as serializers from "../../../../../index";
import { AuthConnectionLocator } from "../../../../../types/AuthConnectionLocator";
import { EnvironmentAuthConnectionLocator } from "../../../../../types/EnvironmentAuthConnectionLocator";
export declare const McpServerConfigUpdateRequestModelAuthConnection: core.serialization.Schema<serializers.conversationalAi.McpServerConfigUpdateRequestModelAuthConnection.Raw, ElevenLabs.conversationalAi.McpServerConfigUpdateRequestModelAuthConnection>;
export declare namespace McpServerConfigUpdateRequestModelAuthConnection {
    type Raw = AuthConnectionLocator.Raw | EnvironmentAuthConnectionLocator.Raw;
}
