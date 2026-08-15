import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
export declare const AstLessThanOrEqualsOperatorNodeInput: core.serialization.ObjectSchema<serializers.AstLessThanOrEqualsOperatorNodeInput.Raw, ElevenLabs.AstLessThanOrEqualsOperatorNodeInput>;
export declare namespace AstLessThanOrEqualsOperatorNodeInput {
    interface Raw {
        left: serializers.AstNodeInput.Raw;
        right: serializers.AstNodeInput.Raw;
    }
}
