import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const DeleteCalendarEventParams: core.serialization.ObjectSchema<serializers.DeleteCalendarEventParams.Raw, ElevenLabs.DeleteCalendarEventParams>;
export declare namespace DeleteCalendarEventParams {
    interface Raw {
        smb_tool_type?: "delete_calendar_event" | null;
    }
}
