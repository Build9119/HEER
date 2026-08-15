/** Whether to include transcript summaries in the response. */
export declare const MessagesTextSearchRequestSummaryMode: {
    readonly Exclude: "exclude";
    readonly Include: "include";
};
export type MessagesTextSearchRequestSummaryMode = (typeof MessagesTextSearchRequestSummaryMode)[keyof typeof MessagesTextSearchRequestSummaryMode];
