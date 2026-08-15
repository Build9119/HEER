import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ConversationAsrUsageModel: core.serialization.ObjectSchema<serializers.ConversationAsrUsageModel.Raw, ElevenLabs.ConversationAsrUsageModel>;
export declare namespace ConversationAsrUsageModel {
    interface Raw {
        asr_model?: string | null;
        total_transcription_calls?: number | null;
        total_audio_input_seconds?: number | null;
    }
}
