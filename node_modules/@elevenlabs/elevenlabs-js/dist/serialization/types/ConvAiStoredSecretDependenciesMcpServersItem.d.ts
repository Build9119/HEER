import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { DependentAvailableMcpServerIdentifier } from "./DependentAvailableMcpServerIdentifier";
import { DependentUnknownMcpServerIdentifier } from "./DependentUnknownMcpServerIdentifier";
export declare const ConvAiStoredSecretDependenciesMcpServersItem: core.serialization.Schema<serializers.ConvAiStoredSecretDependenciesMcpServersItem.Raw, ElevenLabs.ConvAiStoredSecretDependenciesMcpServersItem>;
export declare namespace ConvAiStoredSecretDependenciesMcpServersItem {
    type Raw = ConvAiStoredSecretDependenciesMcpServersItem.Available | ConvAiStoredSecretDependenciesMcpServersItem.Unknown;
    interface Available extends DependentAvailableMcpServerIdentifier.Raw {
        type: "available";
    }
    interface Unknown extends DependentUnknownMcpServerIdentifier.Raw {
        type: "unknown";
    }
}
