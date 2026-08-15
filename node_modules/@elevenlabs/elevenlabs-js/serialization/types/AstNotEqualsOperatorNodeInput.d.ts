import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
export declare const AstNotEqualsOperatorNodeInput: core.serialization.ObjectSchema<serializers.AstNotEqualsOperatorNodeInput.Raw, ElevenLabs.AstNotEqualsOperatorNodeInput>;
export declare namespace AstNotEqualsOperatorNodeInput {
    interface Raw {
        left: serializers.AstNodeInput.Raw;
        right: serializers.AstNodeInput.Raw;
    }
}
