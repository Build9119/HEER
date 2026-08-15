import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ConversationTokenPurpose } from "./ConversationTokenPurpose";
export declare const ConversationTokenResponseModel: core.serialization.ObjectSchema<serializers.ConversationTokenResponseModel.Raw, ElevenLabs.ConversationTokenResponseModel>;
export declare namespace ConversationTokenResponseModel {
    interface Raw {
        agent_id: string;
        conversation_token: string;
        expiration_time_unix_secs?: number | null;
        conversation_id?: string | null;
        purpose: ConversationTokenPurpose.Raw;
        token_requester_user_id?: string | null;
    }
}
