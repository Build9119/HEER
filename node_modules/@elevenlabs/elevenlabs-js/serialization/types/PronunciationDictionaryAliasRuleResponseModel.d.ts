import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const PronunciationDictionaryAliasRuleResponseModel: core.serialization.ObjectSchema<serializers.PronunciationDictionaryAliasRuleResponseModel.Raw, ElevenLabs.PronunciationDictionaryAliasRuleResponseModel>;
export declare namespace PronunciationDictionaryAliasRuleResponseModel {
    interface Raw {
        string_to_replace: string;
        case_sensitive?: boolean | null;
        word_boundaries?: boolean | null;
        alias: string;
    }
}
