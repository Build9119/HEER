import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const UpdateClientParams: core.serialization.ObjectSchema<serializers.UpdateClientParams.Raw, ElevenLabs.UpdateClientParams>;
export declare namespace UpdateClientParams {
    interface Raw {
        smb_tool_type?: "update_client" | null;
    }
}
