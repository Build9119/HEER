/** Token field to extract from the token endpoint response. */
export declare const OAuth2JwtResponseTokenResponseField: {
    readonly AccessToken: "access_token";
    readonly IdToken: "id_token";
};
export type OAuth2JwtResponseTokenResponseField = (typeof OAuth2JwtResponseTokenResponseField)[keyof typeof OAuth2JwtResponseTokenResponseField];
