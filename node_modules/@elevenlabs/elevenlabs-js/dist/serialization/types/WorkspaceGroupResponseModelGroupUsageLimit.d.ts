import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const WorkspaceGroupResponseModelGroupUsageLimit: core.serialization.Schema<serializers.WorkspaceGroupResponseModelGroupUsageLimit.Raw, ElevenLabs.WorkspaceGroupResponseModelGroupUsageLimit>;
export declare namespace WorkspaceGroupResponseModelGroupUsageLimit {
    type Raw = number | "unlimited";
}
