import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const UpdateOrderResponse: core.serialization.ObjectSchema<serializers.UpdateOrderResponse.Raw, ElevenLabs.UpdateOrderResponse>;
export declare namespace UpdateOrderResponse {
    interface Raw {
        name: string;
    }
}
