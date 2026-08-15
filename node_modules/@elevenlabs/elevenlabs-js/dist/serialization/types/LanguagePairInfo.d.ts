import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { LanguageInfo } from "./LanguageInfo";
export declare const LanguagePairInfo: core.serialization.ObjectSchema<serializers.LanguagePairInfo.Raw, ElevenLabs.LanguagePairInfo>;
export declare namespace LanguagePairInfo {
    interface Raw {
        source_language: LanguageInfo.Raw;
        destination_languages: LanguageInfo.Raw[];
    }
}
