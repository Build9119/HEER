/** Version of the turn detection model to use. */
export declare const TurnModel: {
    readonly TurnV2: "turn_v2";
    readonly TurnV3: "turn_v3";
};
export type TurnModel = (typeof TurnModel)[keyof typeof TurnModel];
