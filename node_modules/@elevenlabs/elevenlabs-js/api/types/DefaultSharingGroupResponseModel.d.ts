import type * as ElevenLabs from "../index";
export interface DefaultSharingGroupResponseModel {
    /** The group to share with by default */
    group: ElevenLabs.WorkspaceGroupResponseModel;
    /** The permission level to grant to the group */
    permissionLevel: ElevenLabs.DefaultSharingGroupResponseModelPermissionLevel;
}
