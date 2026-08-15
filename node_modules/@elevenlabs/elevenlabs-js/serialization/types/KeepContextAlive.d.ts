import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const KeepContextAlive: core.serialization.ObjectSchema<serializers.KeepContextAlive.Raw, ElevenLabs.KeepContextAlive>;
export declare namespace KeepContextAlive {
    interface Raw {
        text: "";
        context_id: string;
    }
}
