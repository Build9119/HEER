import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const UpdateServiceParams: core.serialization.ObjectSchema<serializers.UpdateServiceParams.Raw, ElevenLabs.UpdateServiceParams>;
export declare namespace UpdateServiceParams {
    interface Raw {
        smb_tool_type?: "update_service" | null;
    }
}
