import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { EnvironmentVariableAuthConnectionValueRequest } from "./EnvironmentVariableAuthConnectionValueRequest";
export declare const CreateAuthConnectionEnvironmentVariableRequest: core.serialization.ObjectSchema<serializers.CreateAuthConnectionEnvironmentVariableRequest.Raw, ElevenLabs.CreateAuthConnectionEnvironmentVariableRequest>;
export declare namespace CreateAuthConnectionEnvironmentVariableRequest {
    interface Raw {
        label: string;
        values: Record<string, EnvironmentVariableAuthConnectionValueRequest.Raw>;
    }
}
