import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ListStaffParams: core.serialization.ObjectSchema<serializers.ListStaffParams.Raw, ElevenLabs.ListStaffParams>;
export declare namespace ListStaffParams {
    interface Raw {
        list_kwargs?: Record<string, unknown> | null;
        smb_tool_type?: "list_staff" | null;
    }
}
