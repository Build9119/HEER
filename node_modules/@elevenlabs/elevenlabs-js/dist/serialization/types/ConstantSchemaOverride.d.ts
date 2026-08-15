import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ConstantSchemaOverrideConstantValue } from "./ConstantSchemaOverrideConstantValue";
export declare const ConstantSchemaOverride: core.serialization.ObjectSchema<serializers.ConstantSchemaOverride.Raw, ElevenLabs.ConstantSchemaOverride>;
export declare namespace ConstantSchemaOverride {
    interface Raw {
        constant_value: ConstantSchemaOverrideConstantValue.Raw;
    }
}
