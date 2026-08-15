import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ScheduleGroupSessionParams: core.serialization.ObjectSchema<serializers.ScheduleGroupSessionParams.Raw, ElevenLabs.ScheduleGroupSessionParams>;
export declare namespace ScheduleGroupSessionParams {
    interface Raw {
        smb_tool_type?: "schedule_group_session" | null;
    }
}
