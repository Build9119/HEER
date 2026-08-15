import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const DynamicVariableSchemaOverride: core.serialization.ObjectSchema<serializers.DynamicVariableSchemaOverride.Raw, ElevenLabs.DynamicVariableSchemaOverride>;
export declare namespace DynamicVariableSchemaOverride {
    interface Raw {
        dynamic_variable: string;
    }
}
