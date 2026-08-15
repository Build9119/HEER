import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
export declare const AstConditionalOperatorNodeInput: core.serialization.ObjectSchema<serializers.AstConditionalOperatorNodeInput.Raw, ElevenLabs.AstConditionalOperatorNodeInput>;
export declare namespace AstConditionalOperatorNodeInput {
    interface Raw {
        condition: serializers.AstNodeInput.Raw;
        trueExpression: serializers.AstNodeInput.Raw;
        falseExpression: serializers.AstNodeInput.Raw;
    }
}
