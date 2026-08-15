import type * as ElevenLabs from "../index";
/**
 * Execution-related properties for a tool.
 */
export interface ToolExecution {
    taskSupport?: ElevenLabs.ToolExecutionTaskSupport;
    /** Accepts any additional properties */
    [key: string]: any;
}
