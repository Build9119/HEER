import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const FinalOutput: core.serialization.ObjectSchema<serializers.FinalOutput.Raw, ElevenLabs.FinalOutput>;
export declare namespace FinalOutput {
    interface Raw {
        isFinal?: true | null;
    }
}
