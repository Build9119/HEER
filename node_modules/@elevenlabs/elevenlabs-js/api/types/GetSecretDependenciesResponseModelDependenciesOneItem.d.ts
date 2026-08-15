import type * as ElevenLabs from "../index";
export type GetSecretDependenciesResponseModelDependenciesOneItem = ElevenLabs.GetSecretDependenciesResponseModelDependenciesOneItem.Available | ElevenLabs.GetSecretDependenciesResponseModelDependenciesOneItem.Unknown;
export declare namespace GetSecretDependenciesResponseModelDependenciesOneItem {
    interface Available extends ElevenLabs.DependentAvailableAgentIdentifier {
        type: "available";
    }
    interface Unknown extends ElevenLabs.DependentUnknownAgentIdentifier {
        type: "unknown";
    }
}
