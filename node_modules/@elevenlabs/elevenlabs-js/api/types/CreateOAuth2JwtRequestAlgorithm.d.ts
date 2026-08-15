/** JWT signing algorithm */
export declare const CreateOAuth2JwtRequestAlgorithm: {
    readonly Hs256: "HS256";
    readonly Hs384: "HS384";
    readonly Hs512: "HS512";
    readonly Rs256: "RS256";
    readonly Rs384: "RS384";
    readonly Rs512: "RS512";
};
export type CreateOAuth2JwtRequestAlgorithm = (typeof CreateOAuth2JwtRequestAlgorithm)[keyof typeof CreateOAuth2JwtRequestAlgorithm];
