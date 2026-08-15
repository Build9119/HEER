/** The type of word. */
export declare const TranscriptionWordType: {
    readonly Word: "word";
    readonly Spacing: "spacing";
};
export type TranscriptionWordType = (typeof TranscriptionWordType)[keyof typeof TranscriptionWordType];
