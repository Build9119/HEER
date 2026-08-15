/** Strategy for committing transcriptions. */
export declare const SessionStartedPayloadConfigCommitStrategy: {
    readonly Manual: "manual";
    readonly Vad: "vad";
};
export type SessionStartedPayloadConfigCommitStrategy = (typeof SessionStartedPayloadConfigCommitStrategy)[keyof typeof SessionStartedPayloadConfigCommitStrategy];
