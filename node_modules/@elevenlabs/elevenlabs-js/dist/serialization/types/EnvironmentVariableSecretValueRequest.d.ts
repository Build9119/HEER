import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const EnvironmentVariableSecretValueRequest: core.serialization.ObjectSchema<serializers.EnvironmentVariableSecretValueRequest.Raw, ElevenLabs.EnvironmentVariableSecretValueRequest>;
export declare namespace EnvironmentVariableSecretValueRequest {
    interface Raw {
        secret_id: string;
    }
}
