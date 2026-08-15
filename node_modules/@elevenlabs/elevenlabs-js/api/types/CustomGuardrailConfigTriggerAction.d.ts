import type * as ElevenLabs from "../index";
export type CustomGuardrailConfigTriggerAction = ElevenLabs.CustomGuardrailConfigTriggerAction.EndCall | ElevenLabs.CustomGuardrailConfigTriggerAction.Retry;
export declare namespace CustomGuardrailConfigTriggerAction {
    interface EndCall extends ElevenLabs.EndCallTriggerAction {
        type: "end_call";
    }
    interface Retry extends ElevenLabs.RetryTriggerAction {
        type: "retry";
    }
}
