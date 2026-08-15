import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const PronunciationDictionaryPhonemeRuleRequestModel: core.serialization.ObjectSchema<serializers.PronunciationDictionaryPhonemeRuleRequestModel.Raw, ElevenLabs.PronunciationDictionaryPhonemeRuleRequestModel>;
export declare namespace PronunciationDictionaryPhonemeRuleRequestModel {
    interface Raw {
        string_to_replace: string;
        case_sensitive?: boolean | null;
        word_boundaries?: boolean | null;
        phoneme: string;
        alphabet: string;
    }
}
