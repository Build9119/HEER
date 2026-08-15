import type * as ElevenLabs from "../../../../../../../../../api/index";
import * as core from "../../../../../../../../../core";
import type * as serializers from "../../../../../../../../index";
import { UpsertOrderItemRequest } from "../../../../../../../../types/UpsertOrderItemRequest";
export declare const BodyUpsertOrderItemV1ProductionsOrdersOrderIdItemsPost: core.serialization.Schema<serializers.productions.orders.BodyUpsertOrderItemV1ProductionsOrdersOrderIdItemsPost.Raw, ElevenLabs.productions.orders.BodyUpsertOrderItemV1ProductionsOrdersOrderIdItemsPost>;
export declare namespace BodyUpsertOrderItemV1ProductionsOrdersOrderIdItemsPost {
    interface Raw {
        request: UpsertOrderItemRequest.Raw;
    }
}
