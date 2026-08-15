import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ScribeErrorPayload: core.serialization.ObjectSchema<serializers.ScribeErrorPayload.Raw, ElevenLabs.ScribeErrorPayload>;
export declare namespace ScribeErrorPayload {
    interface Raw {
        message_type: "error";
        error: string;
    }
}
