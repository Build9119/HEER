import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { EndCallTriggerAction } from "./EndCallTriggerAction";
import { RetryTriggerAction } from "./RetryTriggerAction";
export declare const ContentGuardrailOutputTriggerAction: core.serialization.Schema<serializers.ContentGuardrailOutputTriggerAction.Raw, ElevenLabs.ContentGuardrailOutputTriggerAction>;
export declare namespace ContentGuardrailOutputTriggerAction {
    type Raw = ContentGuardrailOutputTriggerAction.EndCall | ContentGuardrailOutputTriggerAction.Retry;
    interface EndCall extends EndCallTriggerAction.Raw {
        type: "end_call";
    }
    interface Retry extends RetryTriggerAction.Raw {
        type: "retry";
    }
}
