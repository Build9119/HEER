import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ConversationVoiceUsageModel } from "./ConversationVoiceUsageModel";
export declare const ConversationTtsUsageModel: core.serialization.ObjectSchema<serializers.ConversationTtsUsageModel.Raw, ElevenLabs.ConversationTtsUsageModel>;
export declare namespace ConversationTtsUsageModel {
    interface Raw {
        primary_tts_model?: string | null;
        total_audio_output_seconds?: number | null;
        total_characters?: number | null;
        per_voice_usage?: ConversationVoiceUsageModel.Raw[] | null;
    }
}
