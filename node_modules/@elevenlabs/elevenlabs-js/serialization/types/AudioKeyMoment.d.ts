import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const AudioKeyMoment: core.serialization.ObjectSchema<serializers.AudioKeyMoment.Raw, ElevenLabs.AudioKeyMoment>;
export declare namespace AudioKeyMoment {
    interface Raw {
        timestamp_ms: number;
        type: string;
        description: string;
    }
}
