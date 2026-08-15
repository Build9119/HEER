import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CreateAssetParams: core.serialization.ObjectSchema<serializers.CreateAssetParams.Raw, ElevenLabs.CreateAssetParams>;
export declare namespace CreateAssetParams {
    interface Raw {
        smb_tool_type?: "create_asset" | null;
    }
}
