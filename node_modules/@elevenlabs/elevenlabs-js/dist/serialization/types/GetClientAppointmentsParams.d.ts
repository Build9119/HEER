import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const GetClientAppointmentsParams: core.serialization.ObjectSchema<serializers.GetClientAppointmentsParams.Raw, ElevenLabs.GetClientAppointmentsParams>;
export declare namespace GetClientAppointmentsParams {
    interface Raw {
        smb_tool_type?: "get_client_appointments" | null;
        include_cancelled?: boolean | null;
    }
}
