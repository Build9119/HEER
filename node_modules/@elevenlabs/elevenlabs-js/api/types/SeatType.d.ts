/** Seat types for workspace members. */
export declare const SeatType: {
    readonly WorkspaceAdmin: "workspace_admin";
    readonly WorkspaceMember: "workspace_member";
    readonly WorkspaceLiteMember: "workspace_lite_member";
};
export type SeatType = (typeof SeatType)[keyof typeof SeatType];
