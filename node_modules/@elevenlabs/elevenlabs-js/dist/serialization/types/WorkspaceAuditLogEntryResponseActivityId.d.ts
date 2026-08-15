import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { AccountChangeActivityId } from "./AccountChangeActivityId";
import { AuthenticationActivityId } from "./AuthenticationActivityId";
import { EntityManagementActivityId } from "./EntityManagementActivityId";
import { GroupManagementActivityId } from "./GroupManagementActivityId";
import { UserAccessManagementActivityId } from "./UserAccessManagementActivityId";
export declare const WorkspaceAuditLogEntryResponseActivityId: core.serialization.Schema<serializers.WorkspaceAuditLogEntryResponseActivityId.Raw, ElevenLabs.WorkspaceAuditLogEntryResponseActivityId>;
export declare namespace WorkspaceAuditLogEntryResponseActivityId {
    type Raw = AccountChangeActivityId.Raw | AuthenticationActivityId.Raw | EntityManagementActivityId.Raw | UserAccessManagementActivityId.Raw | GroupManagementActivityId.Raw;
}
