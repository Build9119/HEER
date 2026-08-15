import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const SendTextMulti: core.serialization.ObjectSchema<serializers.SendTextMulti.Raw, ElevenLabs.SendTextMulti>;
export declare namespace SendTextMulti {
    interface Raw {
        text: string;
        context_id?: string | null;
        flush?: boolean | null;
    }
}
