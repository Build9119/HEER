import type * as ElevenLabs from "../index";
export type ContentGuardrailInputTriggerAction = ElevenLabs.ContentGuardrailInputTriggerAction.EndCall | ElevenLabs.ContentGuardrailInputTriggerAction.Retry;
export declare namespace ContentGuardrailInputTriggerAction {
    interface EndCall extends ElevenLabs.EndCallTriggerAction {
        type: "end_call";
    }
    interface Retry extends ElevenLabs.RetryTriggerAction {
        type: "retry";
    }
}
