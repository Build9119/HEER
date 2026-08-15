import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const UpdateOAuth2ClientCredsRequest: core.serialization.ObjectSchema<serializers.UpdateOAuth2ClientCredsRequest.Raw, ElevenLabs.UpdateOAuth2ClientCredsRequest>;
export declare namespace UpdateOAuth2ClientCredsRequest {
    interface Raw {
        provider?: string | null;
        client_id?: string | null;
        scopes?: string[] | null;
        extra_params?: Record<string, string | null | undefined> | null;
        basic_auth_in_header?: boolean | null;
        client_secret?: string | null;
        custom_headers?: Record<string, string | null | undefined> | null;
    }
}
