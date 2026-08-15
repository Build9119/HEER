/** JWT signing algorithm */
export declare const PrivateKeyJwtResponseAlgorithm: {
    readonly Hs256: "HS256";
    readonly Hs384: "HS384";
    readonly Hs512: "HS512";
    readonly Rs256: "RS256";
    readonly Rs384: "RS384";
    readonly Rs512: "RS512";
};
export type PrivateKeyJwtResponseAlgorithm = (typeof PrivateKeyJwtResponseAlgorithm)[keyof typeof PrivateKeyJwtResponseAlgorithm];
