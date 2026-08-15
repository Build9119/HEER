import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
export declare const AstMultiplicationOperatorNodeOutput: core.serialization.ObjectSchema<serializers.AstMultiplicationOperatorNodeOutput.Raw, ElevenLabs.AstMultiplicationOperatorNodeOutput>;
export declare namespace AstMultiplicationOperatorNodeOutput {
    interface Raw {
        left: serializers.AstNodeOutput.Raw;
        right: serializers.AstNodeOutput.Raw;
    }
}
