import type * as ElevenLabs from "../index";
export interface ListOrdersResponse {
    /** The list of orders matching the query. */
    orders: ElevenLabs.OrderSummary[];
}
