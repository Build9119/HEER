import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
export declare const AstMultiplicationOperatorNodeInput: core.serialization.ObjectSchema<serializers.AstMultiplicationOperatorNodeInput.Raw, ElevenLabs.AstMultiplicationOperatorNodeInput>;
export declare namespace AstMultiplicationOperatorNodeInput {
    interface Raw {
        left: serializers.AstNodeInput.Raw;
        right: serializers.AstNodeInput.Raw;
    }
}
