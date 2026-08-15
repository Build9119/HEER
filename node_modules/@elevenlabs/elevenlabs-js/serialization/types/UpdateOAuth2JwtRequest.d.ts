import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { UpdateOAuth2JwtRequestAlgorithm } from "./UpdateOAuth2JwtRequestAlgorithm";
import { UpdateOAuth2JwtRequestTokenResponseField } from "./UpdateOAuth2JwtRequestTokenResponseField";
export declare const UpdateOAuth2JwtRequest: core.serialization.ObjectSchema<serializers.UpdateOAuth2JwtRequest.Raw, ElevenLabs.UpdateOAuth2JwtRequest>;
export declare namespace UpdateOAuth2JwtRequest {
    interface Raw {
        provider?: string | null;
        algorithm?: UpdateOAuth2JwtRequestAlgorithm.Raw | null;
        key_id?: string | null;
        issuer?: string | null;
        audience?: string | null;
        subject?: string | null;
        expiration_seconds?: number | null;
        extra_params?: Record<string, string | null | undefined> | null;
        scopes?: string[] | null;
        token_response_field?: UpdateOAuth2JwtRequestTokenResponseField.Raw | null;
        secret_key?: string | null;
    }
}
