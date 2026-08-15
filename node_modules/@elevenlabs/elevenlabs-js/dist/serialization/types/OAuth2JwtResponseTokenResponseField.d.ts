import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const OAuth2JwtResponseTokenResponseField: core.serialization.Schema<serializers.OAuth2JwtResponseTokenResponseField.Raw, ElevenLabs.OAuth2JwtResponseTokenResponseField>;
export declare namespace OAuth2JwtResponseTokenResponseField {
    type Raw = "access_token" | "id_token";
}
