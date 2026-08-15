import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const GetBookingPageSettingsParams: core.serialization.ObjectSchema<serializers.GetBookingPageSettingsParams.Raw, ElevenLabs.GetBookingPageSettingsParams>;
export declare namespace GetBookingPageSettingsParams {
    interface Raw {
        smb_tool_type?: "get_booking_page_settings" | null;
    }
}
