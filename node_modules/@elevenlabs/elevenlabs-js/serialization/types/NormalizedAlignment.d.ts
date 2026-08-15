import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const NormalizedAlignment: core.serialization.ObjectSchema<serializers.NormalizedAlignment.Raw, ElevenLabs.NormalizedAlignment>;
export declare namespace NormalizedAlignment {
    interface Raw {
        charStartTimesMs?: number[] | null;
        charDurationsMs?: number[] | null;
        chars?: string[] | null;
    }
}
