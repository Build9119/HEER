import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const VideoKeyMoment: core.serialization.ObjectSchema<serializers.VideoKeyMoment.Raw, ElevenLabs.VideoKeyMoment>;
export declare namespace VideoKeyMoment {
    interface Raw {
        timestamp_ms: number;
        type: string;
        description: string;
    }
}
