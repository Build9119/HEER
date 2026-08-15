import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const GetScheduleParams: core.serialization.ObjectSchema<serializers.GetScheduleParams.Raw, ElevenLabs.GetScheduleParams>;
export declare namespace GetScheduleParams {
    interface Raw {
        smb_tool_type?: "get_schedule" | null;
        include_location_filter?: boolean | null;
    }
}
