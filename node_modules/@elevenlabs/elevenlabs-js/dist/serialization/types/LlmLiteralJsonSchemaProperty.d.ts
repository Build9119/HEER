import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { LlmLiteralJsonSchemaPropertyType } from "./LlmLiteralJsonSchemaPropertyType";
export declare const LlmLiteralJsonSchemaProperty: core.serialization.ObjectSchema<serializers.LlmLiteralJsonSchemaProperty.Raw, ElevenLabs.LlmLiteralJsonSchemaProperty>;
export declare namespace LlmLiteralJsonSchemaProperty {
    interface Raw {
        type: LlmLiteralJsonSchemaPropertyType.Raw;
        description: string;
        enum?: string[] | null;
    }
}
