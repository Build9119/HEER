import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const VideoSegment: core.serialization.ObjectSchema<serializers.VideoSegment.Raw, ElevenLabs.VideoSegment>;
export declare namespace VideoSegment {
    interface Raw {
        start_ms: number;
        end_ms: number;
        description: string;
        subjects?: string[] | null;
        shot_type?: string | null;
        camera_movement?: string | null;
        transition_in?: string | null;
        has_speech?: boolean | null;
        has_music?: boolean | null;
        pacing?: string | null;
    }
}
