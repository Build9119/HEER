import type * as ElevenLabs from "../index";
export type ConvAiStoredSecretDependenciesMcpServersItem = ElevenLabs.ConvAiStoredSecretDependenciesMcpServersItem.Available | ElevenLabs.ConvAiStoredSecretDependenciesMcpServersItem.Unknown;
export declare namespace ConvAiStoredSecretDependenciesMcpServersItem {
    interface Available extends ElevenLabs.DependentAvailableMcpServerIdentifier {
        type: "available";
    }
    interface Unknown extends ElevenLabs.DependentUnknownMcpServerIdentifier {
        type: "unknown";
    }
}
