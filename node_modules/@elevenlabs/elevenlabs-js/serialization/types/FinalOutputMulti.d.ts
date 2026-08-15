import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const FinalOutputMulti: core.serialization.ObjectSchema<serializers.FinalOutputMulti.Raw, ElevenLabs.FinalOutputMulti>;
export declare namespace FinalOutputMulti {
    interface Raw {
        isFinal: true;
        contextId?: string | null;
    }
}
