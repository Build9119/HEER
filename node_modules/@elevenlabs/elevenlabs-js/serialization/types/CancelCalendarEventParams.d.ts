import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CancelCalendarEventParams: core.serialization.ObjectSchema<serializers.CancelCalendarEventParams.Raw, ElevenLabs.CancelCalendarEventParams>;
export declare namespace CancelCalendarEventParams {
    interface Raw {
        smb_tool_type?: "cancel_calendar_event" | null;
    }
}
