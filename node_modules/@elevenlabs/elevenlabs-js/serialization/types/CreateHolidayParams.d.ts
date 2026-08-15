import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CreateHolidayParams: core.serialization.ObjectSchema<serializers.CreateHolidayParams.Raw, ElevenLabs.CreateHolidayParams>;
export declare namespace CreateHolidayParams {
    interface Raw {
        smb_tool_type?: "create_holiday" | null;
    }
}
