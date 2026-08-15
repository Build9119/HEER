import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ContentGuardrailInput } from "./ContentGuardrailInput";
import { CustomGuardrailInput } from "./CustomGuardrailInput";
import { FocusGuardrail } from "./FocusGuardrail";
import { PromptInjectionGuardrail } from "./PromptInjectionGuardrail";
export declare const GuardrailsV1Input: core.serialization.ObjectSchema<serializers.GuardrailsV1Input.Raw, ElevenLabs.GuardrailsV1Input>;
export declare namespace GuardrailsV1Input {
    interface Raw {
        version?: "1" | null;
        focus?: FocusGuardrail.Raw | null;
        prompt_injection?: PromptInjectionGuardrail.Raw | null;
        content?: ContentGuardrailInput.Raw | null;
        custom?: CustomGuardrailInput.Raw | null;
    }
}
