import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ConvAiEnvVarLocator } from "./ConvAiEnvVarLocator";
import { ConvAiSecretLocator } from "./ConvAiSecretLocator";
export declare const CustomLlmApiKey: core.serialization.Schema<serializers.CustomLlmApiKey.Raw, ElevenLabs.CustomLlmApiKey>;
export declare namespace CustomLlmApiKey {
    type Raw = ConvAiSecretLocator.Raw | ConvAiEnvVarLocator.Raw;
}
