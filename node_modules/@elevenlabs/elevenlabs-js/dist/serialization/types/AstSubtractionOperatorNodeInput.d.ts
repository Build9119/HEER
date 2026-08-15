import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
export declare const AstSubtractionOperatorNodeInput: core.serialization.ObjectSchema<serializers.AstSubtractionOperatorNodeInput.Raw, ElevenLabs.AstSubtractionOperatorNodeInput>;
export declare namespace AstSubtractionOperatorNodeInput {
    interface Raw {
        left: serializers.AstNodeInput.Raw;
        right: serializers.AstNodeInput.Raw;
    }
}
