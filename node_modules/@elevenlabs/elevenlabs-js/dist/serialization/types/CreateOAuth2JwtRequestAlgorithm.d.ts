import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CreateOAuth2JwtRequestAlgorithm: core.serialization.Schema<serializers.CreateOAuth2JwtRequestAlgorithm.Raw, ElevenLabs.CreateOAuth2JwtRequestAlgorithm>;
export declare namespace CreateOAuth2JwtRequestAlgorithm {
    type Raw = "HS256" | "HS384" | "HS512" | "RS256" | "RS384" | "RS512";
}
