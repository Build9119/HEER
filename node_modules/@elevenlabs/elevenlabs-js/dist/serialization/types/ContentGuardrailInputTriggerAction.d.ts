import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { EndCallTriggerAction } from "./EndCallTriggerAction";
import { RetryTriggerAction } from "./RetryTriggerAction";
export declare const ContentGuardrailInputTriggerAction: core.serialization.Schema<serializers.ContentGuardrailInputTriggerAction.Raw, ElevenLabs.ContentGuardrailInputTriggerAction>;
export declare namespace ContentGuardrailInputTriggerAction {
    type Raw = ContentGuardrailInputTriggerAction.EndCall | ContentGuardrailInputTriggerAction.Retry;
    interface EndCall extends EndCallTriggerAction.Raw {
        type: "end_call";
    }
    interface Retry extends RetryTriggerAction.Raw {
        type: "retry";
    }
}
