/**
 * @example
 *     {
 *         force: true
 *     }
 */
export interface FoldersDeleteRequest {
    /** Force delete. Required for deleting non-empty folders. */
    force?: boolean;
}
