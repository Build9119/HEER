import type * as ElevenLabs from "../index";
export type WorkflowPhoneNumberNodeModelInputPostDialDigits = ElevenLabs.WorkflowPhoneNumberNodeModelInputPostDialDigits.Dynamic | ElevenLabs.WorkflowPhoneNumberNodeModelInputPostDialDigits.Static;
export declare namespace WorkflowPhoneNumberNodeModelInputPostDialDigits {
    interface Dynamic extends ElevenLabs.PostDialDigitsDynamicVariable {
        type: "dynamic";
    }
    interface Static extends ElevenLabs.PostDialDigitsStatic {
        type: "static";
    }
}
