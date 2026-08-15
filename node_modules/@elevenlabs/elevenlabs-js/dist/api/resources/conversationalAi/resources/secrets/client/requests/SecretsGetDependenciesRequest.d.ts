/**
 * @example
 *     {
 *         pageSize: 1,
 *         cursor: "cursor"
 *     }
 */
export interface SecretsGetDependenciesRequest {
    /** How many dependency items to return per page. */
    pageSize?: number;
    /** Used for fetching next page. Cursor is returned in the response. */
    cursor?: string;
}
