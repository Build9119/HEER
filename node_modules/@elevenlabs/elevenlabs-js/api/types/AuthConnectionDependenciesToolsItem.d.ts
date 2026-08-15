import type * as ElevenLabs from "../index";
export type AuthConnectionDependenciesToolsItem = ElevenLabs.AuthConnectionDependenciesToolsItem.Available | ElevenLabs.AuthConnectionDependenciesToolsItem.Unknown;
export declare namespace AuthConnectionDependenciesToolsItem {
    interface Available extends ElevenLabs.DependentAvailableToolIdentifier {
        type: "available";
    }
    interface Unknown extends ElevenLabs.DependentUnknownToolIdentifier {
        type: "unknown";
    }
}
