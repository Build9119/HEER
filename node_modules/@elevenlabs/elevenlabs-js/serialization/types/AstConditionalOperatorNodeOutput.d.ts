import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
export declare const AstConditionalOperatorNodeOutput: core.serialization.ObjectSchema<serializers.AstConditionalOperatorNodeOutput.Raw, ElevenLabs.AstConditionalOperatorNodeOutput>;
export declare namespace AstConditionalOperatorNodeOutput {
    interface Raw {
        condition: serializers.AstNodeOutput.Raw;
        trueExpression: serializers.AstNodeOutput.Raw;
        falseExpression: serializers.AstNodeOutput.Raw;
    }
}
