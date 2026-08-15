import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ScribeSessionTimeLimitExceededErrorPayload: core.serialization.ObjectSchema<serializers.ScribeSessionTimeLimitExceededErrorPayload.Raw, ElevenLabs.ScribeSessionTimeLimitExceededErrorPayload>;
export declare namespace ScribeSessionTimeLimitExceededErrorPayload {
    interface Raw {
        message_type: "session_time_limit_exceeded";
        error: string;
    }
}
