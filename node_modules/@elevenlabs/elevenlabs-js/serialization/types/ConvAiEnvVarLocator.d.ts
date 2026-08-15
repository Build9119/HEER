import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ConvAiEnvVarLocator: core.serialization.ObjectSchema<serializers.ConvAiEnvVarLocator.Raw, ElevenLabs.ConvAiEnvVarLocator>;
export declare namespace ConvAiEnvVarLocator {
    interface Raw {
        env_var_label: string;
    }
}
