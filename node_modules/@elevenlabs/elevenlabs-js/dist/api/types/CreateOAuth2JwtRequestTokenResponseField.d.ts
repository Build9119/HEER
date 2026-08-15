/** Token field to extract from the token endpoint response. */
export declare const CreateOAuth2JwtRequestTokenResponseField: {
    readonly AccessToken: "access_token";
    readonly IdToken: "id_token";
};
export type CreateOAuth2JwtRequestTokenResponseField = (typeof CreateOAuth2JwtRequestTokenResponseField)[keyof typeof CreateOAuth2JwtRequestTokenResponseField];
