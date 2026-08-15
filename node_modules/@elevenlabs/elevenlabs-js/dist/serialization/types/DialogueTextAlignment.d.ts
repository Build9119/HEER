import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const DialogueTextAlignment: core.serialization.ObjectSchema<serializers.DialogueTextAlignment.Raw, ElevenLabs.DialogueTextAlignment>;
export declare namespace DialogueTextAlignment {
    interface Raw {
        chars?: string[] | null;
        char_start_times_ms?: number[] | null;
        char_durations_ms?: number[] | null;
    }
}
