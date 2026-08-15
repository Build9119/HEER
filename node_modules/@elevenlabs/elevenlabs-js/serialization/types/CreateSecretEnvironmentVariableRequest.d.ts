import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { EnvironmentVariableSecretValueRequest } from "./EnvironmentVariableSecretValueRequest";
export declare const CreateSecretEnvironmentVariableRequest: core.serialization.ObjectSchema<serializers.CreateSecretEnvironmentVariableRequest.Raw, ElevenLabs.CreateSecretEnvironmentVariableRequest>;
export declare namespace CreateSecretEnvironmentVariableRequest {
    interface Raw {
        label: string;
        values: Record<string, EnvironmentVariableSecretValueRequest.Raw>;
    }
}
