import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ContentConfig } from "./ContentConfig";
import { ContentGuardrailInputTriggerAction } from "./ContentGuardrailInputTriggerAction";
import { GuardrailExecutionMode } from "./GuardrailExecutionMode";
export declare const ContentGuardrailInput: core.serialization.ObjectSchema<serializers.ContentGuardrailInput.Raw, ElevenLabs.ContentGuardrailInput>;
export declare namespace ContentGuardrailInput {
    interface Raw {
        execution_mode?: GuardrailExecutionMode.Raw | null;
        config?: ContentConfig.Raw | null;
        trigger_action?: ContentGuardrailInputTriggerAction.Raw | null;
    }
}
