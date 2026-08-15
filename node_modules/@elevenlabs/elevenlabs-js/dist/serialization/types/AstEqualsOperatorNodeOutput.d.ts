import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
export declare const AstEqualsOperatorNodeOutput: core.serialization.ObjectSchema<serializers.AstEqualsOperatorNodeOutput.Raw, ElevenLabs.AstEqualsOperatorNodeOutput>;
export declare namespace AstEqualsOperatorNodeOutput {
    interface Raw {
        left: serializers.AstNodeOutput.Raw;
        right: serializers.AstNodeOutput.Raw;
    }
}
