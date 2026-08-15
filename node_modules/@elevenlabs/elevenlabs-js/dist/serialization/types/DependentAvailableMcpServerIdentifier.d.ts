import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { DependentAvailableMcpServerIdentifierAccessLevel } from "./DependentAvailableMcpServerIdentifierAccessLevel";
export declare const DependentAvailableMcpServerIdentifier: core.serialization.ObjectSchema<serializers.DependentAvailableMcpServerIdentifier.Raw, ElevenLabs.DependentAvailableMcpServerIdentifier>;
export declare namespace DependentAvailableMcpServerIdentifier {
    interface Raw {
        id: string;
        name: string;
        created_at_unix_secs: number;
        access_level: DependentAvailableMcpServerIdentifierAccessLevel.Raw;
    }
}
