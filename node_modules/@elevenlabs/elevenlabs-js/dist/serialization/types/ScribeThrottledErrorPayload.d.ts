import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ScribeThrottledErrorPayload: core.serialization.ObjectSchema<serializers.ScribeThrottledErrorPayload.Raw, ElevenLabs.ScribeThrottledErrorPayload>;
export declare namespace ScribeThrottledErrorPayload {
    interface Raw {
        message_type: "commit_throttled";
        error: string;
    }
}
