export declare const MockNoMatchBehavior: {
    readonly CallRealTool: "call_real_tool";
    readonly RaiseError: "raise_error";
};
export type MockNoMatchBehavior = (typeof MockNoMatchBehavior)[keyof typeof MockNoMatchBehavior];
