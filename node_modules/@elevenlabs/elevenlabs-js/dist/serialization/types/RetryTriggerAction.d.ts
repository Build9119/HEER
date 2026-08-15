import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const RetryTriggerAction: core.serialization.ObjectSchema<serializers.RetryTriggerAction.Raw, ElevenLabs.RetryTriggerAction>;
export declare namespace RetryTriggerAction {
    interface Raw {
        feedback?: string | null;
    }
}
