import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const RegisterForGroupSessionParams: core.serialization.ObjectSchema<serializers.RegisterForGroupSessionParams.Raw, ElevenLabs.RegisterForGroupSessionParams>;
export declare namespace RegisterForGroupSessionParams {
    interface Raw {
        smb_tool_type?: "register_for_group_session" | null;
    }
}
