import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { CustomGuardrailConfig } from "./CustomGuardrailConfig";
export declare const CustomGuardrailsConfigOutput: core.serialization.ObjectSchema<serializers.CustomGuardrailsConfigOutput.Raw, ElevenLabs.CustomGuardrailsConfigOutput>;
export declare namespace CustomGuardrailsConfigOutput {
    interface Raw {
        configs?: CustomGuardrailConfig.Raw[] | null;
    }
}
