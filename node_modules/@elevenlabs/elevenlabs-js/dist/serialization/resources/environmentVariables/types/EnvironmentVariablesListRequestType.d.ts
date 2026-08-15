import type * as ElevenLabs from "../../../../api/index";
import * as core from "../../../../core";
import type * as serializers from "../../../index";
export declare const EnvironmentVariablesListRequestType: core.serialization.Schema<serializers.EnvironmentVariablesListRequestType.Raw, ElevenLabs.EnvironmentVariablesListRequestType>;
export declare namespace EnvironmentVariablesListRequestType {
    type Raw = "string" | "secret" | "auth_connection";
}
