import type * as ElevenLabs from "../../../../../index";
/**
 * Auth connection to create
 */
export type AuthConnectionsCreateRequestBody = ElevenLabs.workspace.AuthConnectionsCreateRequestBody.Oauth2ClientCredentials | ElevenLabs.workspace.AuthConnectionsCreateRequestBody.CustomHeaderAuth | ElevenLabs.workspace.AuthConnectionsCreateRequestBody.BasicAuth | ElevenLabs.workspace.AuthConnectionsCreateRequestBody.BearerAuth | ElevenLabs.workspace.AuthConnectionsCreateRequestBody.Oauth2Jwt | ElevenLabs.workspace.AuthConnectionsCreateRequestBody.PrivateKeyJwt | ElevenLabs.workspace.AuthConnectionsCreateRequestBody.Mtls;
export declare namespace AuthConnectionsCreateRequestBody {
    interface Oauth2ClientCredentials extends ElevenLabs.CreateOAuth2ClientCredsRequest {
        authType: "oauth2_client_credentials";
    }
    interface CustomHeaderAuth extends ElevenLabs.CreateCustomHeaderAuthRequest {
        authType: "custom_header_auth";
    }
    interface BasicAuth extends ElevenLabs.CreateBasicAuthRequest {
        authType: "basic_auth";
    }
    interface BearerAuth extends ElevenLabs.CreateBearerAuthRequest {
        authType: "bearer_auth";
    }
    interface Oauth2Jwt extends ElevenLabs.CreateOAuth2JwtRequest {
        authType: "oauth2_jwt";
    }
    interface PrivateKeyJwt extends ElevenLabs.CreatePrivateKeyJwtRequest {
        authType: "private_key_jwt";
    }
    interface Mtls extends ElevenLabs.CreateMtlsAuthRequest {
        authType: "mtls";
    }
}
