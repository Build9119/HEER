import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { Alignment } from "./Alignment";
import { NormalizedAlignment } from "./NormalizedAlignment";
export declare const AudioOutput: core.serialization.ObjectSchema<serializers.AudioOutput.Raw, ElevenLabs.AudioOutput>;
export declare namespace AudioOutput {
    interface Raw {
        audio: string;
        normalizedAlignment?: NormalizedAlignment.Raw | null;
        alignment?: Alignment.Raw | null;
    }
}
