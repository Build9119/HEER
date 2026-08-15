import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const OAuth2JwtResponseAlgorithm: core.serialization.Schema<serializers.OAuth2JwtResponseAlgorithm.Raw, ElevenLabs.OAuth2JwtResponseAlgorithm>;
export declare namespace OAuth2JwtResponseAlgorithm {
    type Raw = "HS256" | "HS384" | "HS512" | "RS256" | "RS384" | "RS512";
}
