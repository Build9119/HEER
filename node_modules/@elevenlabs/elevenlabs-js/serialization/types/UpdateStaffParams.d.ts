import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const UpdateStaffParams: core.serialization.ObjectSchema<serializers.UpdateStaffParams.Raw, ElevenLabs.UpdateStaffParams>;
export declare namespace UpdateStaffParams {
    interface Raw {
        smb_tool_type?: "update_staff" | null;
    }
}
