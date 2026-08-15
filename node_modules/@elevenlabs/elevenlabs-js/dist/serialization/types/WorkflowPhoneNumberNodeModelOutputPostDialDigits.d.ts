import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { PostDialDigitsDynamicVariable } from "./PostDialDigitsDynamicVariable";
import { PostDialDigitsStatic } from "./PostDialDigitsStatic";
export declare const WorkflowPhoneNumberNodeModelOutputPostDialDigits: core.serialization.Schema<serializers.WorkflowPhoneNumberNodeModelOutputPostDialDigits.Raw, ElevenLabs.WorkflowPhoneNumberNodeModelOutputPostDialDigits>;
export declare namespace WorkflowPhoneNumberNodeModelOutputPostDialDigits {
    type Raw = WorkflowPhoneNumberNodeModelOutputPostDialDigits.Dynamic | WorkflowPhoneNumberNodeModelOutputPostDialDigits.Static;
    interface Dynamic extends PostDialDigitsDynamicVariable.Raw {
        type: "dynamic";
    }
    interface Static extends PostDialDigitsStatic.Raw {
        type: "static";
    }
}
