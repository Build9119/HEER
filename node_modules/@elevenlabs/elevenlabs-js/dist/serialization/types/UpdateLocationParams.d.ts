import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const UpdateLocationParams: core.serialization.ObjectSchema<serializers.UpdateLocationParams.Raw, ElevenLabs.UpdateLocationParams>;
export declare namespace UpdateLocationParams {
    interface Raw {
        smb_tool_type?: "update_location" | null;
    }
}
