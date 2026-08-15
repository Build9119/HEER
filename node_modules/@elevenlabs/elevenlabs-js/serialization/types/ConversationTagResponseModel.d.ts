import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ConversationTagResponseModel: core.serialization.ObjectSchema<serializers.ConversationTagResponseModel.Raw, ElevenLabs.ConversationTagResponseModel>;
export declare namespace ConversationTagResponseModel {
    interface Raw {
        tag_id: string;
        workspace_id: string;
        owner_user_id: string;
        title: string;
        description?: string | null;
        created_at_unix_secs: number;
    }
}
