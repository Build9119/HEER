import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ConversationUserResponseModel } from "./ConversationUserResponseModel";
export declare const GetConversationUsersPageResponseModel: core.serialization.ObjectSchema<serializers.GetConversationUsersPageResponseModel.Raw, ElevenLabs.GetConversationUsersPageResponseModel>;
export declare namespace GetConversationUsersPageResponseModel {
    interface Raw {
        users: ConversationUserResponseModel.Raw[];
        next_cursor?: string | null;
        has_more: boolean;
    }
}
