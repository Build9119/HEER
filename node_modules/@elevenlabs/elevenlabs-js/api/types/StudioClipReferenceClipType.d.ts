export declare const StudioClipReferenceClipType: {
    readonly Video: "video";
    readonly Image: "image";
    readonly ExternalAudio: "external_audio";
    readonly TtsNode: "tts_node";
};
export type StudioClipReferenceClipType = (typeof StudioClipReferenceClipType)[keyof typeof StudioClipReferenceClipType];
