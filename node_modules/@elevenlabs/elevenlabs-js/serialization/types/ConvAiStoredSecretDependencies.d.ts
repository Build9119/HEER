import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ConvAiStoredSecretDependenciesAgentsItem } from "./ConvAiStoredSecretDependenciesAgentsItem";
import { ConvAiStoredSecretDependenciesMcpServersItem } from "./ConvAiStoredSecretDependenciesMcpServersItem";
import { ConvAiStoredSecretDependenciesToolsItem } from "./ConvAiStoredSecretDependenciesToolsItem";
import { DependentPhoneNumberIdentifier } from "./DependentPhoneNumberIdentifier";
import { SecretDependencyType } from "./SecretDependencyType";
export declare const ConvAiStoredSecretDependencies: core.serialization.ObjectSchema<serializers.ConvAiStoredSecretDependencies.Raw, ElevenLabs.ConvAiStoredSecretDependencies>;
export declare namespace ConvAiStoredSecretDependencies {
    interface Raw {
        tools: ConvAiStoredSecretDependenciesToolsItem.Raw[];
        tools_has_more?: boolean | null;
        agents: ConvAiStoredSecretDependenciesAgentsItem.Raw[];
        agents_has_more?: boolean | null;
        phone_numbers?: DependentPhoneNumberIdentifier.Raw[] | null;
        phone_numbers_has_more?: boolean | null;
        mcp_servers?: ConvAiStoredSecretDependenciesMcpServersItem.Raw[] | null;
        others: SecretDependencyType.Raw[];
    }
}
