import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const DeleteClientInteractionParams: core.serialization.ObjectSchema<serializers.DeleteClientInteractionParams.Raw, ElevenLabs.DeleteClientInteractionParams>;
export declare namespace DeleteClientInteractionParams {
    interface Raw {
        smb_tool_type?: "delete_client_interaction" | null;
    }
}
