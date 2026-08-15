import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ScribeResourceExhaustedErrorPayload: core.serialization.ObjectSchema<serializers.ScribeResourceExhaustedErrorPayload.Raw, ElevenLabs.ScribeResourceExhaustedErrorPayload>;
export declare namespace ScribeResourceExhaustedErrorPayload {
    interface Raw {
        message_type: "resource_exhausted";
        error: string;
    }
}
