import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CreateStaffParams: core.serialization.ObjectSchema<serializers.CreateStaffParams.Raw, ElevenLabs.CreateStaffParams>;
export declare namespace CreateStaffParams {
    interface Raw {
        smb_tool_type?: "create_staff" | null;
    }
}
