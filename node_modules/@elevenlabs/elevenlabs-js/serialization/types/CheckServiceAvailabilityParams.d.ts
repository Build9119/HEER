import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CheckServiceAvailabilityParams: core.serialization.ObjectSchema<serializers.CheckServiceAvailabilityParams.Raw, ElevenLabs.CheckServiceAvailabilityParams>;
export declare namespace CheckServiceAvailabilityParams {
    interface Raw {
        smb_tool_type?: "check_service_availability" | null;
    }
}
