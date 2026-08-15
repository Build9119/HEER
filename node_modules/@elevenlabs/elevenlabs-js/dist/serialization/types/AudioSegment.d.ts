import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const AudioSegment: core.serialization.ObjectSchema<serializers.AudioSegment.Raw, ElevenLabs.AudioSegment>;
export declare namespace AudioSegment {
    interface Raw {
        start_ms: number;
        end_ms: number;
        description: string;
        segment_type?: string | null;
        has_speech?: boolean | null;
        has_music?: boolean | null;
        pacing?: string | null;
    }
}
