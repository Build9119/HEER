import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { PostDialDigitsDynamicVariable } from "./PostDialDigitsDynamicVariable";
import { PostDialDigitsStatic } from "./PostDialDigitsStatic";
export declare const PhoneNumberTransferPostDialDigits: core.serialization.Schema<serializers.PhoneNumberTransferPostDialDigits.Raw, ElevenLabs.PhoneNumberTransferPostDialDigits>;
export declare namespace PhoneNumberTransferPostDialDigits {
    type Raw = PhoneNumberTransferPostDialDigits.Dynamic | PhoneNumberTransferPostDialDigits.Static;
    interface Dynamic extends PostDialDigitsDynamicVariable.Raw {
        type: "dynamic";
    }
    interface Static extends PostDialDigitsStatic.Raw {
        type: "static";
    }
}
