import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const DeleteStaffParams: core.serialization.ObjectSchema<serializers.DeleteStaffParams.Raw, ElevenLabs.DeleteStaffParams>;
export declare namespace DeleteStaffParams {
    interface Raw {
        smb_tool_type?: "delete_staff" | null;
    }
}
