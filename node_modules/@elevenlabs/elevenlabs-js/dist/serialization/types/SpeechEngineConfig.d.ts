import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { SpeechEngineConfigRequestHeadersValue } from "./SpeechEngineConfigRequestHeadersValue";
export declare const SpeechEngineConfig: core.serialization.ObjectSchema<serializers.SpeechEngineConfig.Raw, ElevenLabs.SpeechEngineConfig>;
export declare namespace SpeechEngineConfig {
    interface Raw {
        ws_url: string;
        request_headers?: Record<string, SpeechEngineConfigRequestHeadersValue.Raw> | null;
    }
}
