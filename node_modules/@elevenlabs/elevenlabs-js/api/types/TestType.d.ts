export declare const TestType: {
    readonly Llm: "llm";
    readonly Tool: "tool";
    readonly Simulation: "simulation";
    readonly Folder: "folder";
};
export type TestType = (typeof TestType)[keyof typeof TestType];
