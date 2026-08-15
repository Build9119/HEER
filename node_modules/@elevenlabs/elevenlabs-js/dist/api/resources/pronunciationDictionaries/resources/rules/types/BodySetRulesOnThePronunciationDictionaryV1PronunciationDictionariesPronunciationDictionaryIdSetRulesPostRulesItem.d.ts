import type * as ElevenLabs from "../../../../../index";
export type BodySetRulesOnThePronunciationDictionaryV1PronunciationDictionariesPronunciationDictionaryIdSetRulesPostRulesItem = ElevenLabs.pronunciationDictionaries.BodySetRulesOnThePronunciationDictionaryV1PronunciationDictionariesPronunciationDictionaryIdSetRulesPostRulesItem.Alias | ElevenLabs.pronunciationDictionaries.BodySetRulesOnThePronunciationDictionaryV1PronunciationDictionariesPronunciationDictionaryIdSetRulesPostRulesItem.Phoneme;
export declare namespace BodySetRulesOnThePronunciationDictionaryV1PronunciationDictionariesPronunciationDictionaryIdSetRulesPostRulesItem {
    interface Alias extends ElevenLabs.PronunciationDictionaryAliasRuleRequestModel {
        type: "alias";
    }
    interface Phoneme extends ElevenLabs.PronunciationDictionaryPhonemeRuleRequestModel {
        type: "phoneme";
    }
}
