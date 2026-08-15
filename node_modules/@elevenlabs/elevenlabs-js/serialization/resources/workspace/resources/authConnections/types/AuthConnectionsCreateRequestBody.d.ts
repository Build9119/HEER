import type * as ElevenLabs from "../../../../../../api/index";
import * as core from "../../../../../../core";
import type * as serializers from "../../../../../index";
import { CreateBasicAuthRequest } from "../../../../../types/CreateBasicAuthRequest";
import { CreateBearerAuthRequest } from "../../../../../types/CreateBearerAuthRequest";
import { CreateCustomHeaderAuthRequest } from "../../../../../types/CreateCustomHeaderAuthRequest";
import { CreateMtlsAuthRequest } from "../../../../../types/CreateMtlsAuthRequest";
import { CreateOAuth2ClientCredsRequest } from "../../../../../types/CreateOAuth2ClientCredsRequest";
import { CreateOAuth2JwtRequest } from "../../../../../types/CreateOAuth2JwtRequest";
import { CreatePrivateKeyJwtRequest } from "../../../../../types/CreatePrivateKeyJwtRequest";
export declare const AuthConnectionsCreateRequestBody: core.serialization.Schema<serializers.workspace.AuthConnectionsCreateRequestBody.Raw, ElevenLabs.workspace.AuthConnectionsCreateRequestBody>;
export declare namespace AuthConnectionsCreateRequestBody {
    type Raw = AuthConnectionsCreateRequestBody.Oauth2ClientCredentials | AuthConnectionsCreateRequestBody.CustomHeaderAuth | AuthConnectionsCreateRequestBody.BasicAuth | AuthConnectionsCreateRequestBody.BearerAuth | AuthConnectionsCreateRequestBody.Oauth2Jwt | AuthConnectionsCreateRequestBody.PrivateKeyJwt | AuthConnectionsCreateRequestBody.Mtls;
    interface Oauth2ClientCredentials extends CreateOAuth2ClientCredsRequest.Raw {
        auth_type: "oauth2_client_credentials";
    }
    interface CustomHeaderAuth extends CreateCustomHeaderAuthRequest.Raw {
        auth_type: "custom_header_auth";
    }
    interface BasicAuth extends CreateBasicAuthRequest.Raw {
        auth_type: "basic_auth";
    }
    interface BearerAuth extends CreateBearerAuthRequest.Raw {
        auth_type: "bearer_auth";
    }
    interface Oauth2Jwt extends CreateOAuth2JwtRequest.Raw {
        auth_type: "oauth2_jwt";
    }
    interface PrivateKeyJwt extends CreatePrivateKeyJwtRequest.Raw {
        auth_type: "private_key_jwt";
    }
    interface Mtls extends CreateMtlsAuthRequest.Raw {
        auth_type: "mtls";
    }
}
