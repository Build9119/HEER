import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ListClientsParams: core.serialization.ObjectSchema<serializers.ListClientsParams.Raw, ElevenLabs.ListClientsParams>;
export declare namespace ListClientsParams {
    interface Raw {
        smb_tool_type?: "list_clients" | null;
    }
}
