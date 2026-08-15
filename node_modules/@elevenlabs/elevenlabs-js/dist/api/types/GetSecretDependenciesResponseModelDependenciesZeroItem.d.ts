import type * as ElevenLabs from "../index";
export type GetSecretDependenciesResponseModelDependenciesZeroItem = ElevenLabs.GetSecretDependenciesResponseModelDependenciesZeroItem.Available | ElevenLabs.GetSecretDependenciesResponseModelDependenciesZeroItem.Unknown;
export declare namespace GetSecretDependenciesResponseModelDependenciesZeroItem {
    interface Available extends ElevenLabs.DependentAvailableToolIdentifier {
        type: "available";
    }
    interface Unknown extends ElevenLabs.DependentUnknownToolIdentifier {
        type: "unknown";
    }
}
