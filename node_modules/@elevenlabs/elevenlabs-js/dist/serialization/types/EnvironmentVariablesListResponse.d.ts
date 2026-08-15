import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { EnvironmentVariableResponse } from "./EnvironmentVariableResponse";
export declare const EnvironmentVariablesListResponse: core.serialization.ObjectSchema<serializers.EnvironmentVariablesListResponse.Raw, ElevenLabs.EnvironmentVariablesListResponse>;
export declare namespace EnvironmentVariablesListResponse {
    interface Raw {
        environment_variables: EnvironmentVariableResponse.Raw[];
        next_cursor?: string | null;
        has_more: boolean;
    }
}
