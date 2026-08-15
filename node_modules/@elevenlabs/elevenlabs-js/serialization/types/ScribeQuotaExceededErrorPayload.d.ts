import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ScribeQuotaExceededErrorPayload: core.serialization.ObjectSchema<serializers.ScribeQuotaExceededErrorPayload.Raw, ElevenLabs.ScribeQuotaExceededErrorPayload>;
export declare namespace ScribeQuotaExceededErrorPayload {
    interface Raw {
        message_type: "quota_exceeded";
        error: string;
    }
}
