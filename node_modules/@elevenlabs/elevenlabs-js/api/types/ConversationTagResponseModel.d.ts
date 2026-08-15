export interface ConversationTagResponseModel {
    tagId: string;
    workspaceId: string;
    ownerUserId: string;
    title: string;
    description?: string;
    createdAtUnixSecs: number;
}
