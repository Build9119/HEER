import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ConversationVoiceRewardModel: core.serialization.ObjectSchema<serializers.ConversationVoiceRewardModel.Raw, ElevenLabs.ConversationVoiceRewardModel>;
export declare namespace ConversationVoiceRewardModel {
    interface Raw {
        voice_id: string;
        reward_usd_cents: number;
    }
}
