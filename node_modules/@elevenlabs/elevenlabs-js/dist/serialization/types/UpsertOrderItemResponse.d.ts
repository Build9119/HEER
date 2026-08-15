import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ItemId } from "./ItemId";
import { QuoteInfo } from "./QuoteInfo";
export declare const UpsertOrderItemResponse: core.serialization.ObjectSchema<serializers.UpsertOrderItemResponse.Raw, ElevenLabs.UpsertOrderItemResponse>;
export declare namespace UpsertOrderItemResponse {
    interface Raw {
        item_id: ItemId.Raw;
        quote?: QuoteInfo.Raw | null;
    }
}
