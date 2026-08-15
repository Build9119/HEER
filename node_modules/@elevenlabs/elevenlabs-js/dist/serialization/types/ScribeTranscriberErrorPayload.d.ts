import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ScribeTranscriberErrorPayload: core.serialization.ObjectSchema<serializers.ScribeTranscriberErrorPayload.Raw, ElevenLabs.ScribeTranscriberErrorPayload>;
export declare namespace ScribeTranscriberErrorPayload {
    interface Raw {
        message_type: "transcriber_error";
        error: string;
    }
}
