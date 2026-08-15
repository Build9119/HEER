import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ContentConfig } from "./ContentConfig";
import { ContentGuardrailOutputTriggerAction } from "./ContentGuardrailOutputTriggerAction";
import { GuardrailExecutionMode } from "./GuardrailExecutionMode";
export declare const ContentGuardrailOutput: core.serialization.ObjectSchema<serializers.ContentGuardrailOutput.Raw, ElevenLabs.ContentGuardrailOutput>;
export declare namespace ContentGuardrailOutput {
    interface Raw {
        execution_mode?: GuardrailExecutionMode.Raw | null;
        config?: ContentConfig.Raw | null;
        trigger_action?: ContentGuardrailOutputTriggerAction.Raw | null;
    }
}
