import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
export declare const AstAdditionOperatorNodeInput: core.serialization.ObjectSchema<serializers.AstAdditionOperatorNodeInput.Raw, ElevenLabs.AstAdditionOperatorNodeInput>;
export declare namespace AstAdditionOperatorNodeInput {
    interface Raw {
        left: serializers.AstNodeInput.Raw;
        right: serializers.AstNodeInput.Raw;
    }
}
