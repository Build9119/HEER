/** Sort mode for listing tests. Use 'folders_first' to place folders before tests. */
export declare const TestsListRequestSortMode: {
    readonly Default: "default";
    readonly FoldersFirst: "folders_first";
};
export type TestsListRequestSortMode = (typeof TestsListRequestSortMode)[keyof typeof TestsListRequestSortMode];
