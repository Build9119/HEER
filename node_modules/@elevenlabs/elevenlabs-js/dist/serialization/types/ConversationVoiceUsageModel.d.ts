import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ConversationVoiceUsageModel: core.serialization.ObjectSchema<serializers.ConversationVoiceUsageModel.Raw, ElevenLabs.ConversationVoiceUsageModel>;
export declare namespace ConversationVoiceUsageModel {
    interface Raw {
        voice_id: string;
        audio_output_seconds?: number | null;
    }
}
