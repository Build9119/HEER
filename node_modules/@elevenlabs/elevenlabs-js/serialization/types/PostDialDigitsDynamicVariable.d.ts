import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const PostDialDigitsDynamicVariable: core.serialization.ObjectSchema<serializers.PostDialDigitsDynamicVariable.Raw, ElevenLabs.PostDialDigitsDynamicVariable>;
export declare namespace PostDialDigitsDynamicVariable {
    interface Raw {
        value: string;
    }
}
