import type * as ElevenLabs from "../../../../api/index";
import * as core from "../../../../core";
import type * as serializers from "../../../index";
import { CreateAuthConnectionEnvironmentVariableRequest } from "../../../types/CreateAuthConnectionEnvironmentVariableRequest";
import { CreateSecretEnvironmentVariableRequest } from "../../../types/CreateSecretEnvironmentVariableRequest";
import { CreateStringEnvironmentVariableRequest } from "../../../types/CreateStringEnvironmentVariableRequest";
export declare const EnvironmentVariablesCreateRequestBody: core.serialization.Schema<serializers.EnvironmentVariablesCreateRequestBody.Raw, ElevenLabs.EnvironmentVariablesCreateRequestBody>;
export declare namespace EnvironmentVariablesCreateRequestBody {
    type Raw = EnvironmentVariablesCreateRequestBody.String | EnvironmentVariablesCreateRequestBody.Secret | EnvironmentVariablesCreateRequestBody.AuthConnection;
    interface String extends CreateStringEnvironmentVariableRequest.Raw {
        type: "string";
    }
    interface Secret extends CreateSecretEnvironmentVariableRequest.Raw {
        type: "secret";
    }
    interface AuthConnection extends CreateAuthConnectionEnvironmentVariableRequest.Raw {
        type: "auth_connection";
    }
}
