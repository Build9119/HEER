import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { LlmLiteralJsonSchemaProperty } from "./LlmLiteralJsonSchemaProperty";
export declare const AstllmNodeOutput: core.serialization.ObjectSchema<serializers.AstllmNodeOutput.Raw, ElevenLabs.AstllmNodeOutput>;
export declare namespace AstllmNodeOutput {
    interface Raw {
        value_schema: LlmLiteralJsonSchemaProperty.Raw;
        prompt: string;
    }
}
