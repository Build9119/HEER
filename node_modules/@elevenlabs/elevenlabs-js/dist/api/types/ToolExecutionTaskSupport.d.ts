export declare const ToolExecutionTaskSupport: {
    readonly Forbidden: "forbidden";
    readonly Optional: "optional";
    readonly Required: "required";
};
export type ToolExecutionTaskSupport = (typeof ToolExecutionTaskSupport)[keyof typeof ToolExecutionTaskSupport];
