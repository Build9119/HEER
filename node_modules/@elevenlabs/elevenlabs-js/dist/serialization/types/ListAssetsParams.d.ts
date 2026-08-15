import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ListAssetsParams: core.serialization.ObjectSchema<serializers.ListAssetsParams.Raw, ElevenLabs.ListAssetsParams>;
export declare namespace ListAssetsParams {
    interface Raw {
        list_kwargs?: Record<string, unknown> | null;
        smb_tool_type?: "list_assets" | null;
    }
}
