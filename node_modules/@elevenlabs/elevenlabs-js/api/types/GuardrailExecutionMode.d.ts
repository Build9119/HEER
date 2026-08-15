export declare const GuardrailExecutionMode: {
    readonly Streaming: "streaming";
    readonly Blocking: "blocking";
};
export type GuardrailExecutionMode = (typeof GuardrailExecutionMode)[keyof typeof GuardrailExecutionMode];
