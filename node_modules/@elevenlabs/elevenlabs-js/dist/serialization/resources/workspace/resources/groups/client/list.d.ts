import type * as ElevenLabs from "../../../../../../api/index";
import * as core from "../../../../../../core";
import type * as serializers from "../../../../../index";
import { WorkspaceGroupResponseModel } from "../../../../../types/WorkspaceGroupResponseModel";
export declare const Response: core.serialization.Schema<serializers.workspace.groups.list.Response.Raw, Record<string, ElevenLabs.WorkspaceGroupResponseModel>>;
export declare namespace Response {
    type Raw = Record<string, WorkspaceGroupResponseModel.Raw>;
}
