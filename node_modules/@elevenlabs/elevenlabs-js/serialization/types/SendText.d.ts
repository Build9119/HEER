import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { GenerationConfig } from "./GenerationConfig";
import { RealtimeVoiceSettings } from "./RealtimeVoiceSettings";
export declare const SendText: core.serialization.ObjectSchema<serializers.SendText.Raw, ElevenLabs.SendText>;
export declare namespace SendText {
    interface Raw {
        text: string;
        try_trigger_generation?: boolean | null;
        voice_settings?: RealtimeVoiceSettings.Raw | null;
        generator_config?: GenerationConfig.Raw | null;
        flush?: boolean | null;
    }
}
