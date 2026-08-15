import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const EnvironmentVariableResponseType: core.serialization.Schema<serializers.EnvironmentVariableResponseType.Raw, ElevenLabs.EnvironmentVariableResponseType>;
export declare namespace EnvironmentVariableResponseType {
    type Raw = "string" | "secret" | "auth_connection";
}
