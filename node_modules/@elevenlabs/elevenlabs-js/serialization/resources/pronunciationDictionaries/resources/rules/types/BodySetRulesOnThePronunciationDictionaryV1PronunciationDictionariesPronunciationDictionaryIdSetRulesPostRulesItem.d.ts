import type * as ElevenLabs from "../../../../../../api/index";
import * as core from "../../../../../../core";
import type * as serializers from "../../../../../index";
import { PronunciationDictionaryAliasRuleRequestModel } from "../../../../../types/PronunciationDictionaryAliasRuleRequestModel";
import { PronunciationDictionaryPhonemeRuleRequestModel } from "../../../../../types/PronunciationDictionaryPhonemeRuleRequestModel";
export declare const BodySetRulesOnThePronunciationDictionaryV1PronunciationDictionariesPronunciationDictionaryIdSetRulesPostRulesItem: core.serialization.Schema<serializers.pronunciationDictionaries.BodySetRulesOnThePronunciationDictionaryV1PronunciationDictionariesPronunciationDictionaryIdSetRulesPostRulesItem.Raw, ElevenLabs.pronunciationDictionaries.BodySetRulesOnThePronunciationDictionaryV1PronunciationDictionariesPronunciationDictionaryIdSetRulesPostRulesItem>;
export declare namespace BodySetRulesOnThePronunciationDictionaryV1PronunciationDictionariesPronunciationDictionaryIdSetRulesPostRulesItem {
    type Raw = BodySetRulesOnThePronunciationDictionaryV1PronunciationDictionariesPronunciationDictionaryIdSetRulesPostRulesItem.Alias | BodySetRulesOnThePronunciationDictionaryV1PronunciationDictionariesPronunciationDictionaryIdSetRulesPostRulesItem.Phoneme;
    interface Alias extends PronunciationDictionaryAliasRuleRequestModel.Raw {
        type: "alias";
    }
    interface Phoneme extends PronunciationDictionaryPhonemeRuleRequestModel.Raw {
        type: "phoneme";
    }
}
