/**
 * Request model for creating Basic Auth connections - inherits common settings and includes sensitive fields
 */
export interface CreateBasicAuthRequest {
    name: string;
    provider: string;
    username: string;
    password: string;
}
