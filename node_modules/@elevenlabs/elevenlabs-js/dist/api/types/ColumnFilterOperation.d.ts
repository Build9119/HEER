export declare const ColumnFilterOperation: {
    readonly In: "in";
    readonly NotIn: "not_in";
    readonly Le: "le";
    readonly Ge: "ge";
    readonly Lt: "lt";
    readonly Gt: "gt";
    readonly Eq: "eq";
    readonly Neq: "neq";
};
export type ColumnFilterOperation = (typeof ColumnFilterOperation)[keyof typeof ColumnFilterOperation];
