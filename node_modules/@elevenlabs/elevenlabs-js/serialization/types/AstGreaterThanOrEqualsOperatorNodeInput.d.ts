import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
export declare const AstGreaterThanOrEqualsOperatorNodeInput: core.serialization.ObjectSchema<serializers.AstGreaterThanOrEqualsOperatorNodeInput.Raw, ElevenLabs.AstGreaterThanOrEqualsOperatorNodeInput>;
export declare namespace AstGreaterThanOrEqualsOperatorNodeInput {
    interface Raw {
        left: serializers.AstNodeInput.Raw;
        right: serializers.AstNodeInput.Raw;
    }
}
