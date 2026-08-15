import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const GenerationConfig: core.serialization.ObjectSchema<serializers.GenerationConfig.Raw, ElevenLabs.GenerationConfig>;
export declare namespace GenerationConfig {
    interface Raw {
        chunk_length_schedule?: number[] | null;
    }
}
