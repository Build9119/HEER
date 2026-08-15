export declare const AssetTranscriptionStatus: {
    readonly Processing: "processing";
    readonly Completed: "completed";
    readonly Failed: "failed";
};
export type AssetTranscriptionStatus = (typeof AssetTranscriptionStatus)[keyof typeof AssetTranscriptionStatus];
