import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
export declare const AstGreaterThanOperatorNodeInput: core.serialization.ObjectSchema<serializers.AstGreaterThanOperatorNodeInput.Raw, ElevenLabs.AstGreaterThanOperatorNodeInput>;
export declare namespace AstGreaterThanOperatorNodeInput {
    interface Raw {
        left: serializers.AstNodeInput.Raw;
        right: serializers.AstNodeInput.Raw;
    }
}
