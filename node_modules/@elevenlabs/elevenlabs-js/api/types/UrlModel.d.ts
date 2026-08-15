/**
 * OCSF URL object.
 *
 * Spec: https://schema.ocsf.io/1.6.0/objects/url
 */
export interface UrlModel {
    /** Full URL string */
    urlString?: string;
    /** URL scheme (e.g., https) */
    scheme?: string;
    /** URL hostname */
    hostname?: string;
    /** URL port */
    port?: number;
    /** URL path */
    path?: string;
    /** URL query string */
    queryString?: string;
}
