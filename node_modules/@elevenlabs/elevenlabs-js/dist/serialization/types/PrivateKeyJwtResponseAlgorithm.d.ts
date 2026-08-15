import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const PrivateKeyJwtResponseAlgorithm: core.serialization.Schema<serializers.PrivateKeyJwtResponseAlgorithm.Raw, ElevenLabs.PrivateKeyJwtResponseAlgorithm>;
export declare namespace PrivateKeyJwtResponseAlgorithm {
    type Raw = "HS256" | "HS384" | "HS512" | "RS256" | "RS384" | "RS512";
}
