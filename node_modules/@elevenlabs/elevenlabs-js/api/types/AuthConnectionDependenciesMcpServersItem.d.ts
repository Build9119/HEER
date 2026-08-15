import type * as ElevenLabs from "../index";
export type AuthConnectionDependenciesMcpServersItem = ElevenLabs.AuthConnectionDependenciesMcpServersItem.Available | ElevenLabs.AuthConnectionDependenciesMcpServersItem.Unknown;
export declare namespace AuthConnectionDependenciesMcpServersItem {
    interface Available extends ElevenLabs.DependentAvailableMcpServerIdentifier {
        type: "available";
    }
    interface Unknown extends ElevenLabs.DependentUnknownMcpServerIdentifier {
        type: "unknown";
    }
}
