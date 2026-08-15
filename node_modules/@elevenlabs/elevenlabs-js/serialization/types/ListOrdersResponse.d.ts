import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { OrderSummary } from "./OrderSummary";
export declare const ListOrdersResponse: core.serialization.ObjectSchema<serializers.ListOrdersResponse.Raw, ElevenLabs.ListOrdersResponse>;
export declare namespace ListOrdersResponse {
    interface Raw {
        orders: OrderSummary.Raw[];
    }
}
