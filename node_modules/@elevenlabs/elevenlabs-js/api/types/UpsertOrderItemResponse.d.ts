import type * as ElevenLabs from "../index";
export interface UpsertOrderItemResponse {
    /** The ID of the upserted order item. */
    itemId: ElevenLabs.ItemId;
    /** The quoted price for this item. */
    quote?: ElevenLabs.QuoteInfo;
}
