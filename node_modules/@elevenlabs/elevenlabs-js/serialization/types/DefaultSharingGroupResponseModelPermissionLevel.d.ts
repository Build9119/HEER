import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const DefaultSharingGroupResponseModelPermissionLevel: core.serialization.Schema<serializers.DefaultSharingGroupResponseModelPermissionLevel.Raw, ElevenLabs.DefaultSharingGroupResponseModelPermissionLevel>;
export declare namespace DefaultSharingGroupResponseModelPermissionLevel {
    type Raw = "admin" | "editor" | "viewer";
}
