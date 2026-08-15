import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ScribeInputErrorPayload: core.serialization.ObjectSchema<serializers.ScribeInputErrorPayload.Raw, ElevenLabs.ScribeInputErrorPayload>;
export declare namespace ScribeInputErrorPayload {
    interface Raw {
        message_type: "input_error";
        error: string;
    }
}
