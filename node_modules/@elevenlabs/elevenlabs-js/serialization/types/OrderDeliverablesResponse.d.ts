import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { DeliverableInfo } from "./DeliverableInfo";
export declare const OrderDeliverablesResponse: core.serialization.ObjectSchema<serializers.OrderDeliverablesResponse.Raw, ElevenLabs.OrderDeliverablesResponse>;
export declare namespace OrderDeliverablesResponse {
    interface Raw {
        deliverables: DeliverableInfo.Raw[];
    }
}
