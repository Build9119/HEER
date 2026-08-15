import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ToolExecutionTaskSupport } from "./ToolExecutionTaskSupport";
export declare const ToolExecution: core.serialization.ObjectSchema<serializers.ToolExecution.Raw, ElevenLabs.ToolExecution>;
export declare namespace ToolExecution {
    interface Raw {
        taskSupport?: ToolExecutionTaskSupport.Raw | null;
        [key: string]: any;
    }
}
