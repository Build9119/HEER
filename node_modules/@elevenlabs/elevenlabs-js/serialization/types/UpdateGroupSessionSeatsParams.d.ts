import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const UpdateGroupSessionSeatsParams: core.serialization.ObjectSchema<serializers.UpdateGroupSessionSeatsParams.Raw, ElevenLabs.UpdateGroupSessionSeatsParams>;
export declare namespace UpdateGroupSessionSeatsParams {
    interface Raw {
        smb_tool_type?: "update_group_session_seats" | null;
    }
}
