import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const EnvironmentVariableAuthConnectionValueRequest: core.serialization.ObjectSchema<serializers.EnvironmentVariableAuthConnectionValueRequest.Raw, ElevenLabs.EnvironmentVariableAuthConnectionValueRequest>;
export declare namespace EnvironmentVariableAuthConnectionValueRequest {
    interface Raw {
        auth_connection_id: string;
    }
}
