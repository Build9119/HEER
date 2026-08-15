import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ListGroupSessionsParams: core.serialization.ObjectSchema<serializers.ListGroupSessionsParams.Raw, ElevenLabs.ListGroupSessionsParams>;
export declare namespace ListGroupSessionsParams {
    interface Raw {
        smb_tool_type?: "list_group_sessions" | null;
    }
}
