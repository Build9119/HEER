import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const UpdateOrderRequest: core.serialization.ObjectSchema<serializers.UpdateOrderRequest.Raw, ElevenLabs.UpdateOrderRequest>;
export declare namespace UpdateOrderRequest {
    interface Raw {
        name: string;
    }
}
