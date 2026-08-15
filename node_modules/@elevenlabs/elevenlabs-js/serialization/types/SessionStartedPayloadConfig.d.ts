import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { AudioFormatEnum } from "./AudioFormatEnum";
import { SessionStartedPayloadConfigCommitStrategy } from "./SessionStartedPayloadConfigCommitStrategy";
export declare const SessionStartedPayloadConfig: core.serialization.ObjectSchema<serializers.SessionStartedPayloadConfig.Raw, ElevenLabs.SessionStartedPayloadConfig>;
export declare namespace SessionStartedPayloadConfig {
    interface Raw {
        sample_rate?: number | null;
        audio_format?: AudioFormatEnum.Raw | null;
        language_code?: string | null;
        commit_strategy?: SessionStartedPayloadConfigCommitStrategy.Raw | null;
        vad_silence_threshold_secs?: number | null;
        vad_threshold?: number | null;
        min_speech_duration_ms?: number | null;
        min_silence_duration_ms?: number | null;
        model_id?: string | null;
        enable_logging?: boolean | null;
        include_timestamps?: boolean | null;
        include_language_detection?: boolean | null;
        keyterms?: string[] | null;
        no_verbatim?: boolean | null;
    }
}
