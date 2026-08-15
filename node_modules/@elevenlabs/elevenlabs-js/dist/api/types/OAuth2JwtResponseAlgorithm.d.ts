/** JWT signing algorithm */
export declare const OAuth2JwtResponseAlgorithm: {
    readonly Hs256: "HS256";
    readonly Hs384: "HS384";
    readonly Hs512: "HS512";
    readonly Rs256: "RS256";
    readonly Rs384: "RS384";
    readonly Rs512: "RS512";
};
export type OAuth2JwtResponseAlgorithm = (typeof OAuth2JwtResponseAlgorithm)[keyof typeof OAuth2JwtResponseAlgorithm];
