import type { BaseClientOptions } from "../../../../BaseClient";
import { type NormalizedClientOptions } from "../../../../BaseClient";
import { OrdersClient } from "../resources/orders/client/Client";
export declare namespace ProductionsClient {
    type Options = BaseClientOptions;
}
export declare class ProductionsClient {
    protected readonly _options: NormalizedClientOptions<ProductionsClient.Options>;
    protected _orders: OrdersClient | undefined;
    constructor(options?: ProductionsClient.Options);
    get orders(): OrdersClient;
}
