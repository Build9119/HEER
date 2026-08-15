import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ScribeRateLimitedErrorPayload: core.serialization.ObjectSchema<serializers.ScribeRateLimitedErrorPayload.Raw, ElevenLabs.ScribeRateLimitedErrorPayload>;
export declare namespace ScribeRateLimitedErrorPayload {
    interface Raw {
        message_type: "rate_limited";
        error: string;
    }
}
