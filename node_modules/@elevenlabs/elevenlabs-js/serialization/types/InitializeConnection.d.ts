import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { GenerationConfig } from "./GenerationConfig";
import { PronunciationDictionaryLocator } from "./PronunciationDictionaryLocator";
import { RealtimeVoiceSettings } from "./RealtimeVoiceSettings";
export declare const InitializeConnection: core.serialization.ObjectSchema<serializers.InitializeConnection.Raw, ElevenLabs.InitializeConnection>;
export declare namespace InitializeConnection {
    interface Raw {
        text: " ";
        voice_settings?: RealtimeVoiceSettings.Raw | null;
        generation_config?: GenerationConfig.Raw | null;
        pronunciation_dictionary_locators?: PronunciationDictionaryLocator.Raw[] | null;
        "xi-api-key"?: string | null;
        authorization?: string | null;
    }
}
