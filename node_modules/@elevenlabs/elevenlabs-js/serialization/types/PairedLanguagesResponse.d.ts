import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { LanguagePairInfo } from "./LanguagePairInfo";
export declare const PairedLanguagesResponse: core.serialization.ObjectSchema<serializers.PairedLanguagesResponse.Raw, ElevenLabs.PairedLanguagesResponse>;
export declare namespace PairedLanguagesResponse {
    interface Raw {
        language_pairs: LanguagePairInfo.Raw[];
    }
}
