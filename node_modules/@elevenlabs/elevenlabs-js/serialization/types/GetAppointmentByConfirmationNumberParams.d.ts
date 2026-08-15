import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const GetAppointmentByConfirmationNumberParams: core.serialization.ObjectSchema<serializers.GetAppointmentByConfirmationNumberParams.Raw, ElevenLabs.GetAppointmentByConfirmationNumberParams>;
export declare namespace GetAppointmentByConfirmationNumberParams {
    interface Raw {
        smb_tool_type?: "get_appointment_by_confirmation_number" | null;
    }
}
