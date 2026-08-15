import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const DeleteProductParams: core.serialization.ObjectSchema<serializers.DeleteProductParams.Raw, ElevenLabs.DeleteProductParams>;
export declare namespace DeleteProductParams {
    interface Raw {
        smb_tool_type?: "delete_product" | null;
    }
}
