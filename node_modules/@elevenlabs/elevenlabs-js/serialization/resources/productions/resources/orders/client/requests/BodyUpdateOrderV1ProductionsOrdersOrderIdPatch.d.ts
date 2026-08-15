import type * as ElevenLabs from "../../../../../../../api/index";
import * as core from "../../../../../../../core";
import type * as serializers from "../../../../../../index";
import { UpdateOrderRequest } from "../../../../../../types/UpdateOrderRequest";
export declare const BodyUpdateOrderV1ProductionsOrdersOrderIdPatch: core.serialization.Schema<serializers.productions.BodyUpdateOrderV1ProductionsOrdersOrderIdPatch.Raw, ElevenLabs.productions.BodyUpdateOrderV1ProductionsOrdersOrderIdPatch>;
export declare namespace BodyUpdateOrderV1ProductionsOrdersOrderIdPatch {
    interface Raw {
        request: UpdateOrderRequest.Raw;
    }
}
