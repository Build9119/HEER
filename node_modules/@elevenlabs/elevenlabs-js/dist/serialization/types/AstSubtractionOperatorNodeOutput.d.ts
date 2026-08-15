import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
export declare const AstSubtractionOperatorNodeOutput: core.serialization.ObjectSchema<serializers.AstSubtractionOperatorNodeOutput.Raw, ElevenLabs.AstSubtractionOperatorNodeOutput>;
export declare namespace AstSubtractionOperatorNodeOutput {
    interface Raw {
        left: serializers.AstNodeOutput.Raw;
        right: serializers.AstNodeOutput.Raw;
    }
}
