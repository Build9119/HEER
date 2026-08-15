import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ListServicesParams: core.serialization.ObjectSchema<serializers.ListServicesParams.Raw, ElevenLabs.ListServicesParams>;
export declare namespace ListServicesParams {
    interface Raw {
        list_kwargs?: Record<string, unknown> | null;
        smb_tool_type?: "list_services" | null;
    }
}
