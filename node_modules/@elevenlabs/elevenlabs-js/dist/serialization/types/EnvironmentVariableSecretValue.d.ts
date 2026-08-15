import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const EnvironmentVariableSecretValue: core.serialization.ObjectSchema<serializers.EnvironmentVariableSecretValue.Raw, ElevenLabs.EnvironmentVariableSecretValue>;
export declare namespace EnvironmentVariableSecretValue {
    interface Raw {
        secret_id: string;
    }
}
