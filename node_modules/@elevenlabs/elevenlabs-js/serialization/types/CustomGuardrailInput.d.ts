import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { CustomGuardrailsConfigInput } from "./CustomGuardrailsConfigInput";
export declare const CustomGuardrailInput: core.serialization.ObjectSchema<serializers.CustomGuardrailInput.Raw, ElevenLabs.CustomGuardrailInput>;
export declare namespace CustomGuardrailInput {
    interface Raw {
        config?: CustomGuardrailsConfigInput.Raw | null;
    }
}
