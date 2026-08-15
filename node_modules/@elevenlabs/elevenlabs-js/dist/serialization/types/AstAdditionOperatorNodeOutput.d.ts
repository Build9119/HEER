import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
export declare const AstAdditionOperatorNodeOutput: core.serialization.ObjectSchema<serializers.AstAdditionOperatorNodeOutput.Raw, ElevenLabs.AstAdditionOperatorNodeOutput>;
export declare namespace AstAdditionOperatorNodeOutput {
    interface Raw {
        left: serializers.AstNodeOutput.Raw;
        right: serializers.AstNodeOutput.Raw;
    }
}
