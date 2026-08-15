import type { BaseClientOptions } from "../../../../../../BaseClient";
import { type NormalizedClientOptions } from "../../../../../../BaseClient";
import { RequestsClient } from "../resources/requests/client/Client";
export declare namespace AnalyticsClient {
    type Options = BaseClientOptions;
}
export declare class AnalyticsClient {
    protected readonly _options: NormalizedClientOptions<AnalyticsClient.Options>;
    protected _requests: RequestsClient | undefined;
    constructor(options?: AnalyticsClient.Options);
    get requests(): RequestsClient;
}
