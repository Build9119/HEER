import type * as ElevenLabs from "../index";
/**
 * Paginated workspace audit log response.
 */
export interface WorkspaceAuditLogsPageResponse {
    entries: ElevenLabs.WorkspaceAuditLogEntryResponse[];
    hasMore: boolean;
    nextCursor?: string;
}
