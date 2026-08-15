import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { CustomGuardrailConfig } from "./CustomGuardrailConfig";
export declare const CustomGuardrailsConfigInput: core.serialization.ObjectSchema<serializers.CustomGuardrailsConfigInput.Raw, ElevenLabs.CustomGuardrailsConfigInput>;
export declare namespace CustomGuardrailsConfigInput {
    interface Raw {
        configs?: CustomGuardrailConfig.Raw[] | null;
    }
}
