import type * as ElevenLabs from "../index";
export interface GetConversationUsersPageResponseModel {
    users: ElevenLabs.ConversationUserResponseModel[];
    nextCursor?: string;
    hasMore: boolean;
}
