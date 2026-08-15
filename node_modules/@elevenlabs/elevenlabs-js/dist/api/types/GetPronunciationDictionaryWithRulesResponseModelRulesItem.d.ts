import type * as ElevenLabs from "../index";
export type GetPronunciationDictionaryWithRulesResponseModelRulesItem = ElevenLabs.GetPronunciationDictionaryWithRulesResponseModelRulesItem.Alias | ElevenLabs.GetPronunciationDictionaryWithRulesResponseModelRulesItem.Phoneme;
export declare namespace GetPronunciationDictionaryWithRulesResponseModelRulesItem {
    interface Alias extends ElevenLabs.PronunciationDictionaryAliasRuleResponseModel {
        type: "alias";
    }
    interface Phoneme extends ElevenLabs.PronunciationDictionaryPhonemeRuleResponseModel {
        type: "phoneme";
    }
}
