import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { EndCallTriggerAction } from "./EndCallTriggerAction";
import { RetryTriggerAction } from "./RetryTriggerAction";
export declare const CustomGuardrailConfigTriggerAction: core.serialization.Schema<serializers.CustomGuardrailConfigTriggerAction.Raw, ElevenLabs.CustomGuardrailConfigTriggerAction>;
export declare namespace CustomGuardrailConfigTriggerAction {
    type Raw = CustomGuardrailConfigTriggerAction.EndCall | CustomGuardrailConfigTriggerAction.Retry;
    interface EndCall extends EndCallTriggerAction.Raw {
        type: "end_call";
    }
    interface Retry extends RetryTriggerAction.Raw {
        type: "retry";
    }
}
