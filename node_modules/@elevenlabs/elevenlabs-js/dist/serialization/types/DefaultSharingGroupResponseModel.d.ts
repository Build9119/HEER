import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { DefaultSharingGroupResponseModelPermissionLevel } from "./DefaultSharingGroupResponseModelPermissionLevel";
import { WorkspaceGroupResponseModel } from "./WorkspaceGroupResponseModel";
export declare const DefaultSharingGroupResponseModel: core.serialization.ObjectSchema<serializers.DefaultSharingGroupResponseModel.Raw, ElevenLabs.DefaultSharingGroupResponseModel>;
export declare namespace DefaultSharingGroupResponseModel {
    interface Raw {
        group: WorkspaceGroupResponseModel.Raw;
        permission_level: DefaultSharingGroupResponseModelPermissionLevel.Raw;
    }
}
