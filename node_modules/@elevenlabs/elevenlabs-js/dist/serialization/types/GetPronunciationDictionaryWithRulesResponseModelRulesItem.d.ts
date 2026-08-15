import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { PronunciationDictionaryAliasRuleResponseModel } from "./PronunciationDictionaryAliasRuleResponseModel";
import { PronunciationDictionaryPhonemeRuleResponseModel } from "./PronunciationDictionaryPhonemeRuleResponseModel";
export declare const GetPronunciationDictionaryWithRulesResponseModelRulesItem: core.serialization.Schema<serializers.GetPronunciationDictionaryWithRulesResponseModelRulesItem.Raw, ElevenLabs.GetPronunciationDictionaryWithRulesResponseModelRulesItem>;
export declare namespace GetPronunciationDictionaryWithRulesResponseModelRulesItem {
    type Raw = GetPronunciationDictionaryWithRulesResponseModelRulesItem.Alias | GetPronunciationDictionaryWithRulesResponseModelRulesItem.Phoneme;
    interface Alias extends PronunciationDictionaryAliasRuleResponseModel.Raw {
        type: "alias";
    }
    interface Phoneme extends PronunciationDictionaryPhonemeRuleResponseModel.Raw {
        type: "phoneme";
    }
}
