export declare const TestSharingMode: {
    readonly All: "all";
    readonly SharedWithMe: "shared_with_me";
};
export type TestSharingMode = (typeof TestSharingMode)[keyof typeof TestSharingMode];
