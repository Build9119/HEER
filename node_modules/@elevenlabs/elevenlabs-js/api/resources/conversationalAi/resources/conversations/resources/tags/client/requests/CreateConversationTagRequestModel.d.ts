/**
 * @example
 *     {
 *         title: "title"
 *     }
 */
export interface CreateConversationTagRequestModel {
    /** Display title of the tag. */
    title: string;
    /** Optional free-text description. */
    description?: string;
}
