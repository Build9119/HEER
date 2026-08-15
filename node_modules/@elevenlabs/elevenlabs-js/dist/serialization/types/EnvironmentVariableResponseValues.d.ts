import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { EnvironmentVariableAuthConnectionValue } from "./EnvironmentVariableAuthConnectionValue";
import { EnvironmentVariableSecretValue } from "./EnvironmentVariableSecretValue";
export declare const EnvironmentVariableResponseValues: core.serialization.Schema<serializers.EnvironmentVariableResponseValues.Raw, ElevenLabs.EnvironmentVariableResponseValues>;
export declare namespace EnvironmentVariableResponseValues {
    type Raw = Record<string, string> | Record<string, EnvironmentVariableSecretValue.Raw> | Record<string, EnvironmentVariableAuthConnectionValue.Raw>;
}
