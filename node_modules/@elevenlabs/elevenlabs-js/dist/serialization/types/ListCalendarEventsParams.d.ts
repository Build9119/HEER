import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ListCalendarEventsParams: core.serialization.ObjectSchema<serializers.ListCalendarEventsParams.Raw, ElevenLabs.ListCalendarEventsParams>;
export declare namespace ListCalendarEventsParams {
    interface Raw {
        smb_tool_type?: "list_calendar_events" | null;
        include_cancelled?: boolean | null;
    }
}
