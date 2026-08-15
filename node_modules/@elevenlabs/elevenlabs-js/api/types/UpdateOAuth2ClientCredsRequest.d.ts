export interface UpdateOAuth2ClientCredsRequest {
    provider?: string;
    clientId?: string;
    scopes?: string[];
    extraParams?: Record<string, string | undefined>;
    basicAuthInHeader?: boolean;
    clientSecret?: string;
    customHeaders?: Record<string, string | undefined>;
}
