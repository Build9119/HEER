export declare const ImageAnalysisStatus: {
    readonly Processing: "processing";
    readonly Completed: "completed";
    readonly Failed: "failed";
};
export type ImageAnalysisStatus = (typeof ImageAnalysisStatus)[keyof typeof ImageAnalysisStatus];
