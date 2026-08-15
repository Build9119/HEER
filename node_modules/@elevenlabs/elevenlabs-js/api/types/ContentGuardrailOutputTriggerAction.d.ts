import type * as ElevenLabs from "../index";
export type ContentGuardrailOutputTriggerAction = ElevenLabs.ContentGuardrailOutputTriggerAction.EndCall | ElevenLabs.ContentGuardrailOutputTriggerAction.Retry;
export declare namespace ContentGuardrailOutputTriggerAction {
    interface EndCall extends ElevenLabs.EndCallTriggerAction {
        type: "end_call";
    }
    interface Retry extends ElevenLabs.RetryTriggerAction {
        type: "retry";
    }
}
