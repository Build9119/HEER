import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ListHolidaysParams: core.serialization.ObjectSchema<serializers.ListHolidaysParams.Raw, ElevenLabs.ListHolidaysParams>;
export declare namespace ListHolidaysParams {
    interface Raw {
        smb_tool_type?: "list_holidays" | null;
    }
}
