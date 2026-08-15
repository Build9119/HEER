import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CancelGroupSessionRegistrationParams: core.serialization.ObjectSchema<serializers.CancelGroupSessionRegistrationParams.Raw, ElevenLabs.CancelGroupSessionRegistrationParams>;
export declare namespace CancelGroupSessionRegistrationParams {
    interface Raw {
        smb_tool_type?: "cancel_group_session_registration" | null;
    }
}
