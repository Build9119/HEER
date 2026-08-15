import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ToolErrorHandlingMode: core.serialization.Schema<serializers.ToolErrorHandlingMode.Raw, ElevenLabs.ToolErrorHandlingMode>;
export declare namespace ToolErrorHandlingMode {
    type Raw = "auto" | "summarized" | "passthrough" | "hide";
}
