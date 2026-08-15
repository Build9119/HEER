import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { RequiredConstraint } from "./RequiredConstraint";
export declare const RequiredConstraints: core.serialization.ObjectSchema<serializers.RequiredConstraints.Raw, ElevenLabs.RequiredConstraints>;
export declare namespace RequiredConstraints {
    interface Raw {
        any_of?: RequiredConstraint.Raw[] | null;
        all_of?: RequiredConstraint.Raw[] | null;
    }
}
