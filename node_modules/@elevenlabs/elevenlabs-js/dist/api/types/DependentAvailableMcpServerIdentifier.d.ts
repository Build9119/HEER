import type * as ElevenLabs from "../index";
export interface DependentAvailableMcpServerIdentifier {
    id: string;
    name: string;
    createdAtUnixSecs: number;
    accessLevel: ElevenLabs.DependentAvailableMcpServerIdentifierAccessLevel;
}
