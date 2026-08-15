import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ListProductsParams: core.serialization.ObjectSchema<serializers.ListProductsParams.Raw, ElevenLabs.ListProductsParams>;
export declare namespace ListProductsParams {
    interface Raw {
        list_kwargs?: Record<string, unknown> | null;
        smb_tool_type?: "list_products" | null;
    }
}
