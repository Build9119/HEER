import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const SayNodePromptMessageInput: core.serialization.ObjectSchema<serializers.SayNodePromptMessageInput.Raw, ElevenLabs.SayNodePromptMessageInput>;
export declare namespace SayNodePromptMessageInput {
    interface Raw {
        type?: "prompt" | null;
        prompt: string;
    }
}
