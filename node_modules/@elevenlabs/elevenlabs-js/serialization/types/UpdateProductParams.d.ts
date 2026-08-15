import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const UpdateProductParams: core.serialization.ObjectSchema<serializers.UpdateProductParams.Raw, ElevenLabs.UpdateProductParams>;
export declare namespace UpdateProductParams {
    interface Raw {
        smb_tool_type?: "update_product" | null;
    }
}
