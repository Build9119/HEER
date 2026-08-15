import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const Alignment: core.serialization.ObjectSchema<serializers.Alignment.Raw, ElevenLabs.Alignment>;
export declare namespace Alignment {
    interface Raw {
        charStartTimesMs?: number[] | null;
        charDurationsMs?: number[] | null;
        chars?: string[] | null;
    }
}
