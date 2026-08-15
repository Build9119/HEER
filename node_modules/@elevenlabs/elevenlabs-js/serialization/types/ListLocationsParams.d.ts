import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ListLocationsParams: core.serialization.ObjectSchema<serializers.ListLocationsParams.Raw, ElevenLabs.ListLocationsParams>;
export declare namespace ListLocationsParams {
    interface Raw {
        smb_tool_type?: "list_locations" | null;
    }
}
