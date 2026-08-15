/**
 * Request model for creating Bearer Auth connections - inherits common settings and includes sensitive fields
 */
export interface CreateBearerAuthRequest {
    name: string;
    provider: string;
    token: string;
}
