import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CreateClientAppointmentParams: core.serialization.ObjectSchema<serializers.CreateClientAppointmentParams.Raw, ElevenLabs.CreateClientAppointmentParams>;
export declare namespace CreateClientAppointmentParams {
    interface Raw {
        smb_tool_type?: "create_client_appointment" | null;
    }
}
