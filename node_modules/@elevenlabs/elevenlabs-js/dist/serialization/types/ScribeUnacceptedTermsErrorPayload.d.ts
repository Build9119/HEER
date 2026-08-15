import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ScribeUnacceptedTermsErrorPayload: core.serialization.ObjectSchema<serializers.ScribeUnacceptedTermsErrorPayload.Raw, ElevenLabs.ScribeUnacceptedTermsErrorPayload>;
export declare namespace ScribeUnacceptedTermsErrorPayload {
    interface Raw {
        message_type: "unaccepted_terms";
        error: string;
    }
}
