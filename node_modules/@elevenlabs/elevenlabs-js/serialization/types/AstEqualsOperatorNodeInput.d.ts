import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
export declare const AstEqualsOperatorNodeInput: core.serialization.ObjectSchema<serializers.AstEqualsOperatorNodeInput.Raw, ElevenLabs.AstEqualsOperatorNodeInput>;
export declare namespace AstEqualsOperatorNodeInput {
    interface Raw {
        left: serializers.AstNodeInput.Raw;
        right: serializers.AstNodeInput.Raw;
    }
}
