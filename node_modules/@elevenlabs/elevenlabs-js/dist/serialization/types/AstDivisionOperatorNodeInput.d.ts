import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
export declare const AstDivisionOperatorNodeInput: core.serialization.ObjectSchema<serializers.AstDivisionOperatorNodeInput.Raw, ElevenLabs.AstDivisionOperatorNodeInput>;
export declare namespace AstDivisionOperatorNodeInput {
    interface Raw {
        left: serializers.AstNodeInput.Raw;
        right: serializers.AstNodeInput.Raw;
    }
}
