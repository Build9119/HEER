import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const VideoSubject: core.serialization.ObjectSchema<serializers.VideoSubject.Raw, ElevenLabs.VideoSubject>;
export declare namespace VideoSubject {
    interface Raw {
        name: string;
        description: string;
    }
}
