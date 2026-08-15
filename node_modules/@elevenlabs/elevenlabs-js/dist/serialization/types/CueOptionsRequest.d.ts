import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CueOptionsRequest: core.serialization.ObjectSchema<serializers.CueOptionsRequest.Raw, ElevenLabs.CueOptionsRequest>;
export declare namespace CueOptionsRequest {
    interface Raw {
        min_duration_ms?: number | null;
        max_duration_ms?: number | null;
        max_lines_per_cue?: number | null;
        max_chars_per_line?: number | null;
        max_chars_per_s?: number | null;
        min_gap_between_cues_frames?: number | null;
    }
}
