import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { LanguageInfo } from "./LanguageInfo";
export declare const SingleLanguagesResponse: core.serialization.ObjectSchema<serializers.SingleLanguagesResponse.Raw, ElevenLabs.SingleLanguagesResponse>;
export declare namespace SingleLanguagesResponse {
    interface Raw {
        languages: LanguageInfo.Raw[];
    }
}
