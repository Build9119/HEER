import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ToolExecutionTaskSupport: core.serialization.Schema<serializers.ToolExecutionTaskSupport.Raw, ElevenLabs.ToolExecutionTaskSupport>;
export declare namespace ToolExecutionTaskSupport {
    type Raw = "forbidden" | "optional" | "required";
}
