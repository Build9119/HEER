import type * as ElevenLabs from "../../../../../../../../../api/index";
import * as core from "../../../../../../../../../core";
import type * as serializers from "../../../../../../../../index";
export declare const CreateConversationTagRequestModel: core.serialization.Schema<serializers.conversationalAi.conversations.CreateConversationTagRequestModel.Raw, ElevenLabs.conversationalAi.conversations.CreateConversationTagRequestModel>;
export declare namespace CreateConversationTagRequestModel {
    interface Raw {
        title: string;
        description?: string | null;
    }
}
