import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const SpeechEngineConversationInitiationClientDataConfig: core.serialization.ObjectSchema<serializers.SpeechEngineConversationInitiationClientDataConfig.Raw, ElevenLabs.SpeechEngineConversationInitiationClientDataConfig>;
export declare namespace SpeechEngineConversationInitiationClientDataConfig {
    interface Raw {
        first_message?: boolean | null;
    }
}
