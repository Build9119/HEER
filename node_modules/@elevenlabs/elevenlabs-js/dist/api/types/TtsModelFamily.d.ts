export declare const TtsModelFamily: {
    /**
     * Deprecated: Use flash instead. */
    readonly Turbo: "turbo";
    readonly Flash: "flash";
    readonly Multilingual: "multilingual";
    readonly V3Conversational: "v3_conversational";
};
export type TtsModelFamily = (typeof TtsModelFamily)[keyof typeof TtsModelFamily];
