import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { CreateOAuth2JwtRequestAlgorithm } from "./CreateOAuth2JwtRequestAlgorithm";
import { CreateOAuth2JwtRequestTokenResponseField } from "./CreateOAuth2JwtRequestTokenResponseField";
export declare const CreateOAuth2JwtRequest: core.serialization.ObjectSchema<serializers.CreateOAuth2JwtRequest.Raw, ElevenLabs.CreateOAuth2JwtRequest>;
export declare namespace CreateOAuth2JwtRequest {
    interface Raw {
        name: string;
        provider: string;
        algorithm?: CreateOAuth2JwtRequestAlgorithm.Raw | null;
        key_id?: string | null;
        issuer: string;
        audience: string;
        subject: string;
        expiration_seconds?: number | null;
        extra_params?: Record<string, string> | null;
        token_url: string;
        scopes?: string[] | null;
        token_response_field?: CreateOAuth2JwtRequestTokenResponseField.Raw | null;
        secret_key: string;
    }
}
