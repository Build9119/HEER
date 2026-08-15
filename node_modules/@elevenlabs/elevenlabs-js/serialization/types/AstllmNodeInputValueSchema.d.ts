import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { LlmLiteralJsonSchemaProperty } from "./LlmLiteralJsonSchemaProperty";
export declare const AstllmNodeInputValueSchema: core.serialization.ObjectSchema<serializers.AstllmNodeInputValueSchema.Raw, ElevenLabs.AstllmNodeInputValueSchema>;
export declare namespace AstllmNodeInputValueSchema {
    interface Raw {
        type?: "llm" | null;
        value_schema: LlmLiteralJsonSchemaProperty.Raw;
    }
}
