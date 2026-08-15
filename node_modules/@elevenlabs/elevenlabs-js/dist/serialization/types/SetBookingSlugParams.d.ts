import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const SetBookingSlugParams: core.serialization.ObjectSchema<serializers.SetBookingSlugParams.Raw, ElevenLabs.SetBookingSlugParams>;
export declare namespace SetBookingSlugParams {
    interface Raw {
        smb_tool_type?: "set_booking_slug" | null;
    }
}
