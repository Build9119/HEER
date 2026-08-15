import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ListClientInteractionsParams: core.serialization.ObjectSchema<serializers.ListClientInteractionsParams.Raw, ElevenLabs.ListClientInteractionsParams>;
export declare namespace ListClientInteractionsParams {
    interface Raw {
        smb_tool_type?: "list_client_interactions" | null;
    }
}
