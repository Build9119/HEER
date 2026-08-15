import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const SearchClientsParams: core.serialization.ObjectSchema<serializers.SearchClientsParams.Raw, ElevenLabs.SearchClientsParams>;
export declare namespace SearchClientsParams {
    interface Raw {
        smb_tool_type?: "search_clients" | null;
    }
}
