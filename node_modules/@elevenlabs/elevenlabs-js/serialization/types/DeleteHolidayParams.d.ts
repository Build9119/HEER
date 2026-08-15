import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const DeleteHolidayParams: core.serialization.ObjectSchema<serializers.DeleteHolidayParams.Raw, ElevenLabs.DeleteHolidayParams>;
export declare namespace DeleteHolidayParams {
    interface Raw {
        smb_tool_type?: "delete_holiday" | null;
    }
}
