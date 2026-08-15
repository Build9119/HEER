import type * as ElevenLabs from "../index";
export interface PairedLanguagesResponse {
    /** The list of available source-to-destination language mappings. */
    languagePairs: ElevenLabs.LanguagePairInfo[];
}
