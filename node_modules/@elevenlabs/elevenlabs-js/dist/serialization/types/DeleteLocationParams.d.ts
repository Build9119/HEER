import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const DeleteLocationParams: core.serialization.ObjectSchema<serializers.DeleteLocationParams.Raw, ElevenLabs.DeleteLocationParams>;
export declare namespace DeleteLocationParams {
    interface Raw {
        smb_tool_type?: "delete_location" | null;
    }
}
