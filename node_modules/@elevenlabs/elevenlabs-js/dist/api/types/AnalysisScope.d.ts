export declare const AnalysisScope: {
    readonly Conversation: "conversation";
    readonly Agent: "agent";
};
export type AnalysisScope = (typeof AnalysisScope)[keyof typeof AnalysisScope];
