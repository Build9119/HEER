import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CreateOAuth2JwtRequestTokenResponseField: core.serialization.Schema<serializers.CreateOAuth2JwtRequestTokenResponseField.Raw, ElevenLabs.CreateOAuth2JwtRequestTokenResponseField>;
export declare namespace CreateOAuth2JwtRequestTokenResponseField {
    type Raw = "access_token" | "id_token";
}
