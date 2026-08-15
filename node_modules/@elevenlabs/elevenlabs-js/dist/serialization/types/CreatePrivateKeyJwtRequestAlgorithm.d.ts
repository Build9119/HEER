import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CreatePrivateKeyJwtRequestAlgorithm: core.serialization.Schema<serializers.CreatePrivateKeyJwtRequestAlgorithm.Raw, ElevenLabs.CreatePrivateKeyJwtRequestAlgorithm>;
export declare namespace CreatePrivateKeyJwtRequestAlgorithm {
    type Raw = "HS256" | "HS384" | "HS512" | "RS256" | "RS384" | "RS512";
}
