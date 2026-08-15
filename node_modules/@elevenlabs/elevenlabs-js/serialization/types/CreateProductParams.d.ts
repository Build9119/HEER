import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CreateProductParams: core.serialization.ObjectSchema<serializers.CreateProductParams.Raw, ElevenLabs.CreateProductParams>;
export declare namespace CreateProductParams {
    interface Raw {
        smb_tool_type?: "create_product" | null;
    }
}
