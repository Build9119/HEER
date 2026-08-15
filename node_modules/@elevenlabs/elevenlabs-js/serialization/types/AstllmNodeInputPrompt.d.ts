import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const AstllmNodeInputPrompt: core.serialization.ObjectSchema<serializers.AstllmNodeInputPrompt.Raw, ElevenLabs.AstllmNodeInputPrompt>;
export declare namespace AstllmNodeInputPrompt {
    interface Raw {
        type?: "llm" | null;
        prompt: string;
    }
}
