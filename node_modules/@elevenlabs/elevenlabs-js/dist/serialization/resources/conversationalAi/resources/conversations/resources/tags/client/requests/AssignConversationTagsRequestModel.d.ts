import type * as ElevenLabs from "../../../../../../../../../api/index";
import * as core from "../../../../../../../../../core";
import type * as serializers from "../../../../../../../../index";
export declare const AssignConversationTagsRequestModel: core.serialization.Schema<serializers.conversationalAi.conversations.AssignConversationTagsRequestModel.Raw, ElevenLabs.conversationalAi.conversations.AssignConversationTagsRequestModel>;
export declare namespace AssignConversationTagsRequestModel {
    interface Raw {
        tag_ids: string[];
    }
}
