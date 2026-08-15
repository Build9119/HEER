import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const DeleteClientParams: core.serialization.ObjectSchema<serializers.DeleteClientParams.Raw, ElevenLabs.DeleteClientParams>;
export declare namespace DeleteClientParams {
    interface Raw {
        smb_tool_type?: "delete_client" | null;
    }
}
