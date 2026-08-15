import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const AssetTranscriptionData: core.serialization.ObjectSchema<serializers.AssetTranscriptionData.Raw, ElevenLabs.AssetTranscriptionData>;
export declare namespace AssetTranscriptionData {
    interface Raw {
        language_code: string;
        text: string;
        words: string[];
        word_start_times_ms: number[];
        word_end_times_ms: number[];
        word_speaker_ids: (string | null | undefined)[];
    }
}
