import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const UpdateOAuth2JwtRequestTokenResponseField: core.serialization.Schema<serializers.UpdateOAuth2JwtRequestTokenResponseField.Raw, ElevenLabs.UpdateOAuth2JwtRequestTokenResponseField>;
export declare namespace UpdateOAuth2JwtRequestTokenResponseField {
    type Raw = "access_token" | "id_token";
}
