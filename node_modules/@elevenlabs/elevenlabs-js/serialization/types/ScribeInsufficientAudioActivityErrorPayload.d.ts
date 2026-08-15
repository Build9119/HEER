import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ScribeInsufficientAudioActivityErrorPayload: core.serialization.ObjectSchema<serializers.ScribeInsufficientAudioActivityErrorPayload.Raw, ElevenLabs.ScribeInsufficientAudioActivityErrorPayload>;
export declare namespace ScribeInsufficientAudioActivityErrorPayload {
    interface Raw {
        message_type: "insufficient_audio_activity";
        error: string;
    }
}
