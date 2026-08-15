import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const UpdateAssetParams: core.serialization.ObjectSchema<serializers.UpdateAssetParams.Raw, ElevenLabs.UpdateAssetParams>;
export declare namespace UpdateAssetParams {
    interface Raw {
        smb_tool_type?: "update_asset" | null;
    }
}
