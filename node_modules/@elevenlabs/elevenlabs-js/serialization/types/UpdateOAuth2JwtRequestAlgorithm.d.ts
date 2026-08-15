import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const UpdateOAuth2JwtRequestAlgorithm: core.serialization.Schema<serializers.UpdateOAuth2JwtRequestAlgorithm.Raw, ElevenLabs.UpdateOAuth2JwtRequestAlgorithm>;
export declare namespace UpdateOAuth2JwtRequestAlgorithm {
    type Raw = "HS256" | "HS384" | "HS512" | "RS256" | "RS384" | "RS512";
}
