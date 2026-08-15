import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CancelGroupSessionForAllParams: core.serialization.ObjectSchema<serializers.CancelGroupSessionForAllParams.Raw, ElevenLabs.CancelGroupSessionForAllParams>;
export declare namespace CancelGroupSessionForAllParams {
    interface Raw {
        smb_tool_type?: "cancel_group_session_for_all" | null;
    }
}
