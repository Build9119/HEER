import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const AudioFormatEnum: core.serialization.Schema<serializers.AudioFormatEnum.Raw, ElevenLabs.AudioFormatEnum>;
export declare namespace AudioFormatEnum {
    type Raw = "pcm_8000" | "pcm_16000" | "pcm_22050" | "pcm_24000" | "pcm_44100" | "pcm_48000" | "ulaw_8000";
}
