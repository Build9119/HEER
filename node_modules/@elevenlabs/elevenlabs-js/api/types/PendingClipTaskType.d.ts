export declare const PendingClipTaskType: {
    readonly Preprocessing: "preprocessing";
    readonly SpeechImport: "speech_import";
    readonly Dubbing: "dubbing";
    readonly VideoToMusic: "video_to_music";
    readonly MediaGeneration: "media_generation";
};
export type PendingClipTaskType = (typeof PendingClipTaskType)[keyof typeof PendingClipTaskType];
