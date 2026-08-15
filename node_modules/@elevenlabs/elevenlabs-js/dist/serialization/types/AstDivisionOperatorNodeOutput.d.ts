import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
export declare const AstDivisionOperatorNodeOutput: core.serialization.ObjectSchema<serializers.AstDivisionOperatorNodeOutput.Raw, ElevenLabs.AstDivisionOperatorNodeOutput>;
export declare namespace AstDivisionOperatorNodeOutput {
    interface Raw {
        left: serializers.AstNodeOutput.Raw;
        right: serializers.AstNodeOutput.Raw;
    }
}
