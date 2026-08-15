import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
export declare const WorkflowExpressionConditionModelInput: core.serialization.ObjectSchema<serializers.WorkflowExpressionConditionModelInput.Raw, ElevenLabs.WorkflowExpressionConditionModelInput>;
export declare namespace WorkflowExpressionConditionModelInput {
    interface Raw {
        label?: string | null;
        expression: serializers.AstNodeInput.Raw;
    }
}
