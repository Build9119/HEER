export declare const AudioAnalysisStatus: {
    readonly Processing: "processing";
    readonly Completed: "completed";
    readonly Failed: "failed";
};
export type AudioAnalysisStatus = (typeof AudioAnalysisStatus)[keyof typeof AudioAnalysisStatus];
