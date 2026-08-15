import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { AuthConnectionDependenciesMcpServersItem } from "./AuthConnectionDependenciesMcpServersItem";
import { AuthConnectionDependenciesToolsItem } from "./AuthConnectionDependenciesToolsItem";
import { DependentIntegrationConnectionIdentifier } from "./DependentIntegrationConnectionIdentifier";
export declare const AuthConnectionDependencies: core.serialization.ObjectSchema<serializers.AuthConnectionDependencies.Raw, ElevenLabs.AuthConnectionDependencies>;
export declare namespace AuthConnectionDependencies {
    interface Raw {
        tools?: AuthConnectionDependenciesToolsItem.Raw[] | null;
        mcp_servers?: AuthConnectionDependenciesMcpServersItem.Raw[] | null;
        integration_connections?: DependentIntegrationConnectionIdentifier.Raw[] | null;
    }
}
