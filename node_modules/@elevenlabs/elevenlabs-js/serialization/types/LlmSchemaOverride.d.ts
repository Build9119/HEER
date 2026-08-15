import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const LlmSchemaOverride: core.serialization.ObjectSchema<serializers.LlmSchemaOverride.Raw, ElevenLabs.LlmSchemaOverride>;
export declare namespace LlmSchemaOverride {
    interface Raw {
        prompt?: string | null;
    }
}
