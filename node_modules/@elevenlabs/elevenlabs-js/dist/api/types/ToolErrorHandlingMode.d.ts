/** Controls how tool errors are processed before being shared with the agent. */
export declare const ToolErrorHandlingMode: {
    readonly Auto: "auto";
    readonly Summarized: "summarized";
    readonly Passthrough: "passthrough";
    readonly Hide: "hide";
};
export type ToolErrorHandlingMode = (typeof ToolErrorHandlingMode)[keyof typeof ToolErrorHandlingMode];
