export declare const Currency: {
    readonly Usd: "usd";
    readonly Eur: "eur";
    readonly Inr: "inr";
    readonly Pln: "pln";
};
export type Currency = (typeof Currency)[keyof typeof Currency];
