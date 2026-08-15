import type * as ElevenLabs from "../index";
export type WorkflowPhoneNumberNodeModelOutputPostDialDigits = ElevenLabs.WorkflowPhoneNumberNodeModelOutputPostDialDigits.Dynamic | ElevenLabs.WorkflowPhoneNumberNodeModelOutputPostDialDigits.Static;
export declare namespace WorkflowPhoneNumberNodeModelOutputPostDialDigits {
    interface Dynamic extends ElevenLabs.PostDialDigitsDynamicVariable {
        type: "dynamic";
    }
    interface Static extends ElevenLabs.PostDialDigitsStatic {
        type: "static";
    }
}
