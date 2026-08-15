import type * as ElevenLabs from "../../../../api/index";
import * as core from "../../../../core";
import type * as serializers from "../../../index";
import { EnvironmentVariableAuthConnectionValueRequest } from "../../../types/EnvironmentVariableAuthConnectionValueRequest";
import { EnvironmentVariableSecretValueRequest } from "../../../types/EnvironmentVariableSecretValueRequest";
export declare const UpdateEnvironmentVariableRequestValuesValue: core.serialization.Schema<serializers.UpdateEnvironmentVariableRequestValuesValue.Raw, ElevenLabs.UpdateEnvironmentVariableRequestValuesValue>;
export declare namespace UpdateEnvironmentVariableRequestValuesValue {
    type Raw = string | EnvironmentVariableSecretValueRequest.Raw | EnvironmentVariableAuthConnectionValueRequest.Raw;
}
