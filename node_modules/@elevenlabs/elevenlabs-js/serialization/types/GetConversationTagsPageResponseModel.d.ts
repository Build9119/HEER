import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ConversationTagResponseModel } from "./ConversationTagResponseModel";
export declare const GetConversationTagsPageResponseModel: core.serialization.ObjectSchema<serializers.GetConversationTagsPageResponseModel.Raw, ElevenLabs.GetConversationTagsPageResponseModel>;
export declare namespace GetConversationTagsPageResponseModel {
    interface Raw {
        conversation_tags: ConversationTagResponseModel.Raw[];
        next_cursor?: string | null;
        has_more: boolean;
    }
}
