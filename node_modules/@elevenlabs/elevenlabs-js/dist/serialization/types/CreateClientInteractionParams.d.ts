import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CreateClientInteractionParams: core.serialization.ObjectSchema<serializers.CreateClientInteractionParams.Raw, ElevenLabs.CreateClientInteractionParams>;
export declare namespace CreateClientInteractionParams {
    interface Raw {
        smb_tool_type?: "create_client_interaction" | null;
    }
}
