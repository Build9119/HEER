import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const UpdateCalendarEventParams: core.serialization.ObjectSchema<serializers.UpdateCalendarEventParams.Raw, ElevenLabs.UpdateCalendarEventParams>;
export declare namespace UpdateCalendarEventParams {
    interface Raw {
        smb_tool_type?: "update_calendar_event" | null;
    }
}
