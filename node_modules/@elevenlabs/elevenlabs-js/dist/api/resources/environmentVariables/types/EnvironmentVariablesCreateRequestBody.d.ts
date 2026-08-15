import type * as ElevenLabs from "../../../index";
export type EnvironmentVariablesCreateRequestBody = ElevenLabs.EnvironmentVariablesCreateRequestBody.String | ElevenLabs.EnvironmentVariablesCreateRequestBody.Secret | ElevenLabs.EnvironmentVariablesCreateRequestBody.AuthConnection;
export declare namespace EnvironmentVariablesCreateRequestBody {
    interface String extends ElevenLabs.CreateStringEnvironmentVariableRequest {
        type: "string";
    }
    interface Secret extends ElevenLabs.CreateSecretEnvironmentVariableRequest {
        type: "secret";
    }
    interface AuthConnection extends ElevenLabs.CreateAuthConnectionEnvironmentVariableRequest {
        type: "auth_connection";
    }
}
