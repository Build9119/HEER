import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ScribeQueueOverflowErrorPayload: core.serialization.ObjectSchema<serializers.ScribeQueueOverflowErrorPayload.Raw, ElevenLabs.ScribeQueueOverflowErrorPayload>;
export declare namespace ScribeQueueOverflowErrorPayload {
    interface Raw {
        message_type: "queue_overflow";
        error: string;
    }
}
