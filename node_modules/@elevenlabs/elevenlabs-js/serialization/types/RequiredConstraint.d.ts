import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const RequiredConstraint: core.serialization.ObjectSchema<serializers.RequiredConstraint.Raw, ElevenLabs.RequiredConstraint>;
export declare namespace RequiredConstraint {
    interface Raw {
        required: string[];
    }
}
