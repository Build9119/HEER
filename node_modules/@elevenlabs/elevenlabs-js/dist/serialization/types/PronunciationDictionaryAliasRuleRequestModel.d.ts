import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const PronunciationDictionaryAliasRuleRequestModel: core.serialization.ObjectSchema<serializers.PronunciationDictionaryAliasRuleRequestModel.Raw, ElevenLabs.PronunciationDictionaryAliasRuleRequestModel>;
export declare namespace PronunciationDictionaryAliasRuleRequestModel {
    interface Raw {
        string_to_replace: string;
        case_sensitive?: boolean | null;
        word_boundaries?: boolean | null;
        alias: string;
    }
}
