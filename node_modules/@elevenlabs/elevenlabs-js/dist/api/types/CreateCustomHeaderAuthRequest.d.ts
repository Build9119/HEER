export interface CreateCustomHeaderAuthRequest {
    name: string;
    provider: string;
    /** The name of the header to use for authentication (e.g., 'x-api-key') */
    headerName: string;
    token: string;
}
