import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const FocusGuardrail: core.serialization.ObjectSchema<serializers.FocusGuardrail.Raw, ElevenLabs.FocusGuardrail>;
export declare namespace FocusGuardrail {
    interface Raw {
        is_enabled?: boolean | null;
    }
}
