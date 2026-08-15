import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const DependentAvailableMcpServerIdentifierAccessLevel: core.serialization.Schema<serializers.DependentAvailableMcpServerIdentifierAccessLevel.Raw, ElevenLabs.DependentAvailableMcpServerIdentifierAccessLevel>;
export declare namespace DependentAvailableMcpServerIdentifierAccessLevel {
    type Raw = "admin" | "editor" | "commenter" | "viewer";
}
