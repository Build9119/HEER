import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const UpdateHolidayParams: core.serialization.ObjectSchema<serializers.UpdateHolidayParams.Raw, ElevenLabs.UpdateHolidayParams>;
export declare namespace UpdateHolidayParams {
    interface Raw {
        smb_tool_type?: "update_holiday" | null;
    }
}
