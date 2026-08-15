import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const EnvironmentVariableAuthConnectionValue: core.serialization.ObjectSchema<serializers.EnvironmentVariableAuthConnectionValue.Raw, ElevenLabs.EnvironmentVariableAuthConnectionValue>;
export declare namespace EnvironmentVariableAuthConnectionValue {
    interface Raw {
        auth_connection_id: string;
    }
}
