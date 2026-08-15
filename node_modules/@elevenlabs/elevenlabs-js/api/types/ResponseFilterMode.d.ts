/** Controls how tool responses are filtered before being visible to the agent. */
export declare const ResponseFilterMode: {
    readonly All: "all";
    readonly Allow: "allow";
    readonly HideAll: "hide_all";
};
export type ResponseFilterMode = (typeof ResponseFilterMode)[keyof typeof ResponseFilterMode];
