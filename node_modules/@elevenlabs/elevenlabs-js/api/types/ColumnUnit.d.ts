export declare const ColumnUnit: {
    readonly Ms: "ms";
    readonly S: "s";
    readonly Min: "min";
    readonly Duration: "duration";
    readonly Credits: "credits";
    readonly Usd: "usd";
    readonly Eur: "eur";
    readonly Inr: "inr";
    readonly Pln: "pln";
    readonly Ratio: "ratio";
    readonly Rating: "rating";
};
export type ColumnUnit = (typeof ColumnUnit)[keyof typeof ColumnUnit];
