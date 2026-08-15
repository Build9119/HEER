/** The permission level to grant to the group */
export declare const DefaultSharingGroupResponseModelPermissionLevel: {
    readonly Admin: "admin";
    readonly Editor: "editor";
    readonly Viewer: "viewer";
};
export type DefaultSharingGroupResponseModelPermissionLevel = (typeof DefaultSharingGroupResponseModelPermissionLevel)[keyof typeof DefaultSharingGroupResponseModelPermissionLevel];
