export declare const AnalysisPropertyType: {
    readonly Boolean: "boolean";
    readonly String: "string";
    readonly Integer: "integer";
    readonly Number: "number";
};
export type AnalysisPropertyType = (typeof AnalysisPropertyType)[keyof typeof AnalysisPropertyType];
