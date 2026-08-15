import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const PronunciationDictionaryLocator: core.serialization.ObjectSchema<serializers.PronunciationDictionaryLocator.Raw, ElevenLabs.PronunciationDictionaryLocator>;
export declare namespace PronunciationDictionaryLocator {
    interface Raw {
        pronunciation_dictionary_id: string;
        version_id: string;
    }
}
