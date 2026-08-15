import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { GenerationConfig } from "./GenerationConfig";
import { PronunciationDictionaryLocator } from "./PronunciationDictionaryLocator";
import { RealtimeVoiceSettings } from "./RealtimeVoiceSettings";
export declare const InitializeConnectionMulti: core.serialization.ObjectSchema<serializers.InitializeConnectionMulti.Raw, ElevenLabs.InitializeConnectionMulti>;
export declare namespace InitializeConnectionMulti {
    interface Raw {
        text: " ";
        voice_settings?: RealtimeVoiceSettings.Raw | null;
        generation_config?: GenerationConfig.Raw | null;
        pronunciation_dictionary_locators?: PronunciationDictionaryLocator.Raw[] | null;
        xi_api_key?: string | null;
        authorization?: string | null;
        context_id?: string | null;
    }
}
