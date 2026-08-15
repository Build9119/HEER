import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ActorModel } from "./ActorModel";
import { DeviceModel } from "./DeviceModel";
import { HttpRequestModel } from "./HttpRequestModel";
import { SeverityId } from "./SeverityId";
import { StatusId } from "./StatusId";
import { WorkspaceAuditLogEntryResponseActivityId } from "./WorkspaceAuditLogEntryResponseActivityId";
export declare const WorkspaceAuditLogEntryResponse: core.serialization.ObjectSchema<serializers.WorkspaceAuditLogEntryResponse.Raw, ElevenLabs.WorkspaceAuditLogEntryResponse>;
export declare namespace WorkspaceAuditLogEntryResponse {
    interface Raw {
        metadata?: Record<string, unknown> | null;
        time?: number | null;
        activity_id: WorkspaceAuditLogEntryResponseActivityId.Raw;
        activity_name: string;
        category_name?: string | null;
        category_uid?: number | null;
        class_name?: string | null;
        class_uid?: number | null;
        severity_id?: SeverityId.Raw | null;
        status_id: StatusId.Raw;
        actor: ActorModel.Raw;
        device?: DeviceModel.Raw | null;
        http_request?: HttpRequestModel.Raw | null;
        message: string;
        unmapped?: Record<string, unknown> | null;
        id: string;
        time_dt?: string | null;
        type_uid?: number | null;
        type_name?: string | null;
    }
}
