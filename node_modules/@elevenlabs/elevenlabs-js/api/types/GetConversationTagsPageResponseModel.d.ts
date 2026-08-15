import type * as ElevenLabs from "../index";
export interface GetConversationTagsPageResponseModel {
    conversationTags: ElevenLabs.ConversationTagResponseModel[];
    nextCursor?: string;
    hasMore: boolean;
}
