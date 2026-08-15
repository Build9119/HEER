import type * as ElevenLabs from "../../../../../../../../../api/index";
import * as core from "../../../../../../../../../core";
import type * as serializers from "../../../../../../../../index";
export declare const PatchConversationTagRequestModel: core.serialization.Schema<serializers.conversationalAi.conversations.PatchConversationTagRequestModel.Raw, ElevenLabs.conversationalAi.conversations.PatchConversationTagRequestModel>;
export declare namespace PatchConversationTagRequestModel {
    interface Raw {
        title?: string | null;
        description?: string | null;
    }
}
