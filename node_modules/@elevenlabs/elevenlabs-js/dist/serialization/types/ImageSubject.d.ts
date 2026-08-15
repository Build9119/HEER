import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ImageSubject: core.serialization.ObjectSchema<serializers.ImageSubject.Raw, ElevenLabs.ImageSubject>;
export declare namespace ImageSubject {
    interface Raw {
        name: string;
        description: string;
    }
}
