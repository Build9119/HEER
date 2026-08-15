/**
 * Request model for creating mTLS auth connections.
 */
export interface CreateMtlsAuthRequest {
    name: string;
    provider: string;
    clientCertificate: string;
    clientKey: string;
    caCertificate?: string;
    keyPassphrase?: string;
}
