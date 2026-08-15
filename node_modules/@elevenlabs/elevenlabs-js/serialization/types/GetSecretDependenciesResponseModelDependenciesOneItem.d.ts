import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { DependentAvailableAgentIdentifier } from "./DependentAvailableAgentIdentifier";
import { DependentUnknownAgentIdentifier } from "./DependentUnknownAgentIdentifier";
export declare const GetSecretDependenciesResponseModelDependenciesOneItem: core.serialization.Schema<serializers.GetSecretDependenciesResponseModelDependenciesOneItem.Raw, ElevenLabs.GetSecretDependenciesResponseModelDependenciesOneItem>;
export declare namespace GetSecretDependenciesResponseModelDependenciesOneItem {
    type Raw = GetSecretDependenciesResponseModelDependenciesOneItem.Available | GetSecretDependenciesResponseModelDependenciesOneItem.Unknown;
    interface Available extends DependentAvailableAgentIdentifier.Raw {
        type: "available";
    }
    interface Unknown extends DependentUnknownAgentIdentifier.Raw {
        type: "unknown";
    }
}
