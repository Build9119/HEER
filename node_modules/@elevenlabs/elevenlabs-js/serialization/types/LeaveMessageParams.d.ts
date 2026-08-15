import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const LeaveMessageParams: core.serialization.ObjectSchema<serializers.LeaveMessageParams.Raw, ElevenLabs.LeaveMessageParams>;
export declare namespace LeaveMessageParams {
    interface Raw {
        smb_tool_type?: "leave_message" | null;
    }
}
