import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { Alignment } from "./Alignment";
import { NormalizedAlignment } from "./NormalizedAlignment";
export declare const AudioOutputMulti: core.serialization.ObjectSchema<serializers.AudioOutputMulti.Raw, ElevenLabs.AudioOutputMulti>;
export declare namespace AudioOutputMulti {
    interface Raw {
        audio: string;
        normalizedAlignment?: NormalizedAlignment.Raw | null;
        alignment?: Alignment.Raw | null;
        contextId?: string | null;
    }
}
