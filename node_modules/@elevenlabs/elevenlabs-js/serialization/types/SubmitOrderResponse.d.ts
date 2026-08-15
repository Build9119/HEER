import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { OrderId } from "./OrderId";
import { OrderState } from "./OrderState";
export declare const SubmitOrderResponse: core.serialization.ObjectSchema<serializers.SubmitOrderResponse.Raw, ElevenLabs.SubmitOrderResponse>;
export declare namespace SubmitOrderResponse {
    interface Raw {
        order_id: OrderId.Raw;
        state: OrderState.Raw;
        submitted_at: string;
    }
}
