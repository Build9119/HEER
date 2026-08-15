export declare const VideoAnalysisStatus: {
    readonly Processing: "processing";
    readonly Completed: "completed";
    readonly Failed: "failed";
};
export type VideoAnalysisStatus = (typeof VideoAnalysisStatus)[keyof typeof VideoAnalysisStatus];
