export declare const MockingStrategy: {
    readonly All: "all";
    readonly Selected: "selected";
    readonly None: "none";
};
export type MockingStrategy = (typeof MockingStrategy)[keyof typeof MockingStrategy];
