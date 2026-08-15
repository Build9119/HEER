import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const InputAudioChunkPayload: core.serialization.ObjectSchema<serializers.InputAudioChunkPayload.Raw, ElevenLabs.InputAudioChunkPayload>;
export declare namespace InputAudioChunkPayload {
    interface Raw {
        message_type: "input_audio_chunk";
        audio_base_64: string;
        commit: boolean;
        sample_rate: number;
        previous_text?: string | null;
    }
}
