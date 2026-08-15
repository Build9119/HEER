import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { Icon } from "./Icon";
import { ToolAnnotations } from "./ToolAnnotations";
import { ToolExecution } from "./ToolExecution";
export declare const Tool: core.serialization.ObjectSchema<serializers.Tool.Raw, ElevenLabs.Tool>;
export declare namespace Tool {
    interface Raw {
        name: string;
        title?: string | null;
        description?: string | null;
        inputSchema: Record<string, unknown>;
        outputSchema?: Record<string, unknown> | null;
        icons?: Icon.Raw[] | null;
        annotations?: ToolAnnotations.Raw | null;
        _meta?: Record<string, unknown> | null;
        execution?: ToolExecution.Raw | null;
        [key: string]: any;
    }
}
