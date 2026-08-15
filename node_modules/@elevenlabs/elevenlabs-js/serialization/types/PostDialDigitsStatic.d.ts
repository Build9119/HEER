import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const PostDialDigitsStatic: core.serialization.ObjectSchema<serializers.PostDialDigitsStatic.Raw, ElevenLabs.PostDialDigitsStatic>;
export declare namespace PostDialDigitsStatic {
    interface Raw {
        value: string;
    }
}
