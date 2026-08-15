import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { EnvironmentVariableResponseType } from "./EnvironmentVariableResponseType";
import { EnvironmentVariableResponseValues } from "./EnvironmentVariableResponseValues";
export declare const EnvironmentVariableResponse: core.serialization.ObjectSchema<serializers.EnvironmentVariableResponse.Raw, ElevenLabs.EnvironmentVariableResponse>;
export declare namespace EnvironmentVariableResponse {
    interface Raw {
        label: string;
        created_at_unix_secs: number;
        updated_at_unix_secs: number;
        created_by_user_id?: string | null;
        type: EnvironmentVariableResponseType.Raw;
        id: string;
        workspace_id: string;
        values: EnvironmentVariableResponseValues.Raw;
    }
}
