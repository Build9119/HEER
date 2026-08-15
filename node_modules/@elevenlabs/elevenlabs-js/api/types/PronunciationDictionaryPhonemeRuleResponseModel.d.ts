export interface PronunciationDictionaryPhonemeRuleResponseModel {
    stringToReplace: string;
    /** Whether the rule matches case-sensitively. */
    caseSensitive?: boolean;
    /** Whether the rule only matches at word boundaries. */
    wordBoundaries?: boolean;
    phoneme: string;
    alphabet: string;
}
