import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const DeleteServiceParams: core.serialization.ObjectSchema<serializers.DeleteServiceParams.Raw, ElevenLabs.DeleteServiceParams>;
export declare namespace DeleteServiceParams {
    interface Raw {
        smb_tool_type?: "delete_service" | null;
    }
}
