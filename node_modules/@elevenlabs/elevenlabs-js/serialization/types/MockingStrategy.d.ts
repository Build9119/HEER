import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const MockingStrategy: core.serialization.Schema<serializers.MockingStrategy.Raw, ElevenLabs.MockingStrategy>;
export declare namespace MockingStrategy {
    type Raw = "all" | "selected" | "none";
}
