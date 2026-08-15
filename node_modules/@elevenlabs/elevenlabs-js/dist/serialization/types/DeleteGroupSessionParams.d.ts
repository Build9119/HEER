import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const DeleteGroupSessionParams: core.serialization.ObjectSchema<serializers.DeleteGroupSessionParams.Raw, ElevenLabs.DeleteGroupSessionParams>;
export declare namespace DeleteGroupSessionParams {
    interface Raw {
        smb_tool_type?: "delete_group_session" | null;
    }
}
