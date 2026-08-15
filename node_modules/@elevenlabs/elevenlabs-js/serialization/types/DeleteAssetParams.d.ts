import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const DeleteAssetParams: core.serialization.ObjectSchema<serializers.DeleteAssetParams.Raw, ElevenLabs.DeleteAssetParams>;
export declare namespace DeleteAssetParams {
    interface Raw {
        smb_tool_type?: "delete_asset" | null;
    }
}
