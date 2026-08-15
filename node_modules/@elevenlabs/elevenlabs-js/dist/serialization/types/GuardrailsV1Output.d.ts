import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ContentGuardrailOutput } from "./ContentGuardrailOutput";
import { CustomGuardrailOutput } from "./CustomGuardrailOutput";
import { FocusGuardrail } from "./FocusGuardrail";
import { PromptInjectionGuardrail } from "./PromptInjectionGuardrail";
export declare const GuardrailsV1Output: core.serialization.ObjectSchema<serializers.GuardrailsV1Output.Raw, ElevenLabs.GuardrailsV1Output>;
export declare namespace GuardrailsV1Output {
    interface Raw {
        version?: "1" | null;
        focus?: FocusGuardrail.Raw | null;
        prompt_injection?: PromptInjectionGuardrail.Raw | null;
        content?: ContentGuardrailOutput.Raw | null;
        custom?: CustomGuardrailOutput.Raw | null;
    }
}
