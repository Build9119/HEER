import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { WorkspaceAuditLogEntryResponse } from "./WorkspaceAuditLogEntryResponse";
export declare const WorkspaceAuditLogsPageResponse: core.serialization.ObjectSchema<serializers.WorkspaceAuditLogsPageResponse.Raw, ElevenLabs.WorkspaceAuditLogsPageResponse>;
export declare namespace WorkspaceAuditLogsPageResponse {
    interface Raw {
        entries: WorkspaceAuditLogEntryResponse.Raw[];
        has_more: boolean;
        next_cursor?: string | null;
    }
}
