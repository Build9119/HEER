import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { CustomGuardrailsConfigOutput } from "./CustomGuardrailsConfigOutput";
export declare const CustomGuardrailOutput: core.serialization.ObjectSchema<serializers.CustomGuardrailOutput.Raw, ElevenLabs.CustomGuardrailOutput>;
export declare namespace CustomGuardrailOutput {
    interface Raw {
        config?: CustomGuardrailsConfigOutput.Raw | null;
    }
}
