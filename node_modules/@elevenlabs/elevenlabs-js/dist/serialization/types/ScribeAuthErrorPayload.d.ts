import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ScribeAuthErrorPayload: core.serialization.ObjectSchema<serializers.ScribeAuthErrorPayload.Raw, ElevenLabs.ScribeAuthErrorPayload>;
export declare namespace ScribeAuthErrorPayload {
    interface Raw {
        message_type: "auth_error";
        error: string;
    }
}
