import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const PromptInjectionGuardrail: core.serialization.ObjectSchema<serializers.PromptInjectionGuardrail.Raw, ElevenLabs.PromptInjectionGuardrail>;
export declare namespace PromptInjectionGuardrail {
    interface Raw {
        is_enabled?: boolean | null;
    }
}
