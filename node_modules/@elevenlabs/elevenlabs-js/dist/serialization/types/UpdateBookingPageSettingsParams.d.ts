import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const UpdateBookingPageSettingsParams: core.serialization.ObjectSchema<serializers.UpdateBookingPageSettingsParams.Raw, ElevenLabs.UpdateBookingPageSettingsParams>;
export declare namespace UpdateBookingPageSettingsParams {
    interface Raw {
        smb_tool_type?: "update_booking_page_settings" | null;
    }
}
