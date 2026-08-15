export declare const TestRunMetadataTestType: {
    readonly Llm: "llm";
    readonly ToolCall: "tool_call";
    readonly Simulation: "simulation";
};
export type TestRunMetadataTestType = (typeof TestRunMetadataTestType)[keyof typeof TestRunMetadataTestType];
