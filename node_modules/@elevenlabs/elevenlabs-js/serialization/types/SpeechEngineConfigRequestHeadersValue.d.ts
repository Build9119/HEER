import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ConvAiDynamicVariable } from "./ConvAiDynamicVariable";
import { ConvAiSecretLocator } from "./ConvAiSecretLocator";
export declare const SpeechEngineConfigRequestHeadersValue: core.serialization.Schema<serializers.SpeechEngineConfigRequestHeadersValue.Raw, ElevenLabs.SpeechEngineConfigRequestHeadersValue>;
export declare namespace SpeechEngineConfigRequestHeadersValue {
    type Raw = string | ConvAiSecretLocator.Raw | ConvAiDynamicVariable.Raw;
}
