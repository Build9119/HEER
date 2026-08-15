/**
 * @example
 *     {
 *         entityIds: ["entity_ids"]
 *     }
 */
export interface BodyBulkMoveTestsToFolderV1ConvaiAgentTestingBulkMovePost {
    /** The IDs of tests or folders to move. */
    entityIds: string[];
    /** The folder to move the entities to. If not set, the entities will be moved to the root folder. */
    moveTo?: string;
}
