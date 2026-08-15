import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const PronunciationDictionaryPhonemeRuleResponseModel: core.serialization.ObjectSchema<serializers.PronunciationDictionaryPhonemeRuleResponseModel.Raw, ElevenLabs.PronunciationDictionaryPhonemeRuleResponseModel>;
export declare namespace PronunciationDictionaryPhonemeRuleResponseModel {
    interface Raw {
        string_to_replace: string;
        case_sensitive?: boolean | null;
        word_boundaries?: boolean | null;
        phoneme: string;
        alphabet: string;
    }
}
