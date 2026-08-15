import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const GetBookingSlugStatusParams: core.serialization.ObjectSchema<serializers.GetBookingSlugStatusParams.Raw, ElevenLabs.GetBookingSlugStatusParams>;
export declare namespace GetBookingSlugStatusParams {
    interface Raw {
        smb_tool_type?: "get_booking_slug_status" | null;
    }
}
