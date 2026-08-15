import type * as ElevenLabs from "../index";
export type PhoneNumberTransferPostDialDigits = ElevenLabs.PhoneNumberTransferPostDialDigits.Dynamic | ElevenLabs.PhoneNumberTransferPostDialDigits.Static;
export declare namespace PhoneNumberTransferPostDialDigits {
    interface Dynamic extends ElevenLabs.PostDialDigitsDynamicVariable {
        type: "dynamic";
    }
    interface Static extends ElevenLabs.PostDialDigitsStatic {
        type: "static";
    }
}
