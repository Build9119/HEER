import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const SayNodePromptMessageOutput: core.serialization.ObjectSchema<serializers.SayNodePromptMessageOutput.Raw, ElevenLabs.SayNodePromptMessageOutput>;
export declare namespace SayNodePromptMessageOutput {
    interface Raw {
        type: "prompt";
        prompt: string;
    }
}
