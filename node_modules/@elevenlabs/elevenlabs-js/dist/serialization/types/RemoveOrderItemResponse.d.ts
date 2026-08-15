import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const RemoveOrderItemResponse: core.serialization.ObjectSchema<serializers.RemoveOrderItemResponse.Raw, ElevenLabs.RemoveOrderItemResponse>;
export declare namespace RemoveOrderItemResponse {
    interface Raw {
        success: boolean;
    }
}
