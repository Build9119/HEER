import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { PostDialDigitsDynamicVariable } from "./PostDialDigitsDynamicVariable";
import { PostDialDigitsStatic } from "./PostDialDigitsStatic";
export declare const WorkflowPhoneNumberNodeModelInputPostDialDigits: core.serialization.Schema<serializers.WorkflowPhoneNumberNodeModelInputPostDialDigits.Raw, ElevenLabs.WorkflowPhoneNumberNodeModelInputPostDialDigits>;
export declare namespace WorkflowPhoneNumberNodeModelInputPostDialDigits {
    type Raw = WorkflowPhoneNumberNodeModelInputPostDialDigits.Dynamic | WorkflowPhoneNumberNodeModelInputPostDialDigits.Static;
    interface Dynamic extends PostDialDigitsDynamicVariable.Raw {
        type: "dynamic";
    }
    interface Static extends PostDialDigitsStatic.Raw {
        type: "static";
    }
}
